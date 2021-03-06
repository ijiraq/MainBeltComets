__author__ = 'jjk, mtb55'

import itertools
import os
import re
import struct
import sys
import time
import logging

from datetime import datetime
from astropy import coordinates

try:
    from astropy.time import sofa_time
except ImportError:
    from astropy.time import erfa_time as sofa_time
try:
    from astropy.coordinates import ICRSCoordinates
except ImportError:
    from astropy.coordinates import ICRS as ICRSCoordinates
from astropy.time import TimeString
from astropy.time import Time
from astropy import units
import numpy

import storage


DEFAULT_OBSERVERS = ['M. T. Bannister', 'J. J. Kavelaars']
DEFAULT_TELESCOPE = "CFHT 3.6m + CCD"
DEFAULT_ASTROMETRIC_NETWORK = "UCAC4"

MPCNOTES = {"Note1": {" ": " ",
                      "": " ",
                      "*": "*",
                      "A": "earlier approximate position inferior",
                      "a": "sense of motion ambiguous",
                      "B": "bright sky/black or dark plate",
                      "b": "bad seeing",
                      "c": "crowded star field",
                      "D": "declination uncertain",
                      "d": "diffuse image",
                      "E": "at or near edge of plate",
                      "F": "faint image",
                      "f": "involved with emulsion or plate flaw",
                      "G": "poor guiding",
                      "g": "no guiding",
                      "H": "hand measurement of CCD image",
                      "I": "involved with star",
                      "i": "inkdot measured",
                      "J": "J2000.0 rereduction of previously-reported position",
                      "K": "stacked image",
                      "k": "stare-mode observation by scanning system",
                      "M": "measurement difficult",
                      "m": "image tracked on object motion",
                      "N": "near edge of plate, measurement uncertain",
                      "O": "image out of focus",
                      "o": "plate measured in one direction only",
                      "P": "position uncertain",
                      "p": "poor image",
                      "R": "right ascension uncertain",
                      "r": "poor distribution of reference stars",
                      "S": "poor sky",
                      "s": "streaked image",
                      "T": "time uncertain",
                      "t": "trailed image",
                      "U": "uncertain image",
                      "u": "unconfirmed image",
                      "V": "very faint image",
                      "W": "weak image",
                      "w": "weak solution"},
            "Note2": {" ": " ",
                      "": " ",
                      "P": "Photographic",
                      "e": "Encoder",
                      "C": "CCD",
                      "T": "Meridian or transit circle",
                      "M": "Micrometer",
                      "V": "'Roving Observer' observation",
                      "R": "Radar observation",
                      "S": "Satellite observation",
                      "c": "Corrected-without-republication CCD observation",
                      "E": "Occultation-derived observations",
                      "O": "Offset observations (used only for observations of natural satellites)",
                      "H": "Hipparcos geocentric observations",
                      "N": "Normal place",
                      "n": "Mini-normal place derived from averaging observations from video frames"},
            'PhotometryNote': {" ": " ",
                               "": " ",
                               "L": "Photometry uncertainty lacking",
                               "Y": "Photometry measured successfully",
                               "Z": "Photometry measurement failed."}}


class NullObservation(object):

    NULL_OBSERVATION_CHARACTERS = ["!", "-", "#"]

    def __init__(self, null_observation=None, null_observation_character=None):
        """
        A boolean object that keeps track of True/False status via a set of magic characters.
        """
        if null_observation_character is None:
            null_observation_character = NullObservation.NULL_OBSERVATION_CHARACTERS[0]
        self.null_observation_character = null_observation_character

        if isinstance(null_observation, basestring):
            self._null_observation = str(null_observation)[0] in NullObservation.NULL_OBSERVATION_CHARACTERS
        elif isinstance(null_observation, bool):
            self._null_observation = null_observation
        else:
            self._null_observation = False

    def __str__(self):
        return self._null_observation and self.null_observation_character or " "

    def __bool__(self):
        return self._null_observation

    def __nonzero__(self):
        return self.__bool__()


class MPCFormatError(Exception):
    """Base class for errors in MPC formatting."""


class TNOdbFlags(object):
    """
    The OSSOS/CFEPS database has a 'flag' field that indicates OSSOS specific issues associated with an
    MPC formatted line in the database.
    """

    def __init__(self, flags):

        if not re.match("[10]{12}", flags):
            raise ValueError("illegal flag string: {}".format(flags))
        self.__flags = flags

    def __str__(self):
        return self.__flags

    @property
    def is_discovery(self):
        """
        Is this observation part of the discovery triplet?  bit 1
        :return: bool
        """
        return self.__flags[0] == 1

    @is_discovery.setter
    def is_discovery(self, is_discovery):
        self.__flags[0] == bool(is_discovery) and "1" or "0"

    @property
    def is_secret(self):
        """
        Is this observation secret? bit 2
        :return: bool
        """
        return self.__flags[1] == 1



class MPCFieldFormatError(MPCFormatError):
    def __init__(self, field, requirement, actual):
        super(MPCFieldFormatError, self).__init__(
            "Field %s: %s; but was %s" % (field, requirement, actual))


def format_ra_dec(ra_deg, dec_deg):
    """
    Converts RA and DEC values from degrees into the formatting required
    by the Minor Planet Center:

    Formats:
      RA: 'HH MM SS.ddd'
      DEC: 'sDD MM SS.dd' (with 's' being the sign)

    (From: http://www.minorplanetcenter.net/iau/info/OpticalObs.html)

    Args:
      ra_deg: float
        Right ascension in degrees
      dec_deg: float
        Declination in degrees

    Returns:
      formatted_ra: str
      formatted_dec: str
    """
    coords = ICRSCoordinates(ra=ra_deg, dec=dec_deg,
                             unit=(units.degree, units.degree))

    # decimal=False results in using sexagesimal form
    formatted_ra = coords.ra.format(unit=units.hour, decimal=False,
                                    sep=" ", precision=3, alwayssign=False,
                                    pad=True)

    formatted_dec = coords.dec.format(unit=units.degree, decimal=False,
                                      sep=" ", precision=2, alwayssign=True,
                                      pad=True)

    return formatted_ra, formatted_dec


class MPCNote(object):
    """
    Alphabetic note shown with some of the observations. Non-alphabetic codes are used to differentiate between
    different programs at the same site and such codes will be defined in the headings for the individual
    observatories in the Minor Planet Circulars.
    """

    def __init__(self, code="C", note_type="Note2"):
        self._note_type = None
        self._code = None
        self.note_type = note_type
        self.code = code

    @property
    def note_type(self):
        """
        Note 1 or 2 from an MPC line.
        """
        return self._note_type

    @note_type.setter
    def note_type(self, note_type):
        if note_type not in MPCNOTES.keys():
            raise ValueError("Invalid note_type: expected one of %s got %s" % (str(MPCNOTES.keys()), note_type))
        self._note_type = note_type

    @property
    def code(self):
        """
        The MPC note the denotes the type of detector system used
        """
        return self._code

    @code.setter
    def code(self, code):
        """

        :type code: str
        :param code: an MPC Note code. Either from the allow dictionary or 0-9
        """
        if code is None:
            _code = " "
        else:
            _code = str(code).strip()

        if _code.isdigit():
            if self.note_type != 'Note1':
                raise MPCFieldFormatError(self.note_type,
                                          "Must be a character",
                                          _code)
            if not 0 < int(_code) < 10:
                print 0, _code, 10
                print 0 < int(_code) < 10
                raise MPCFieldFormatError(self.note_type,
                                          "numeric value must be between 0 and 9",
                                          _code)
        else:
            if len(_code) > 1:
                raise MPCFieldFormatError(self.note_type,
                                          "must be 0 or 1 characters",
                                          _code)
            if _code not in MPCNOTES[self.note_type]:
                raise MPCFieldFormatError(self.note_type,
                                          "must one of " + str(MPCNOTES[self.note_type]),
                                          _code)
        self._code = _code

    def __str__(self):
        return str(self.code)

    @property
    def long(self):
        return MPCNOTES[self.note_type][self.code]


class Discovery(object):
    """
    Holds the discovery flag for an MPC Observation Line
    """

    def __init__(self, is_discovery=False):
        self._is_discovery = False
        self._is_initial_discovery = False
        self.is_discovery = is_discovery
        self.is_initial_discovery = is_discovery

    def set_from_mpc_line(self, mpc_line):
        """
        Given an MPC line set the discovery object
        """
        mpc_line = str(mpc_line)
        if len(mpc_line) < 56:
            raise MPCFieldFormatError("mpc_line",
                                      "is too short",
                                      mpc_line)
        self.is_discovery = mpc_line[12]

    @property
    def is_initial_discovery(self):
        return self._is_initial_discovery

    @property
    def is_discovery(self):
        return self._is_discovery

    @is_discovery.setter
    def is_discovery(self, is_discovery):
        if is_discovery not in ['*', '&', ' ', '', True, False, None]:
            raise MPCFieldFormatError("discovery",
                                      "must be one of '',' ','&', '*',True, False. Was: ",
                                      is_discovery)
        self._is_discovery = (is_discovery in ['*', '&', True] and True) or False

    @is_initial_discovery.setter
    def is_initial_discovery(self, is_discovery):
        """
        Is this MPC line the initial discovery line?
        @param is_discovery: the code for the discovery setting "*" or True or False
        """
        self._is_initial_discovery = (is_discovery in ["*", True] and True) or False

    def __str__(self):
        if self.is_initial_discovery:
            return "*"
        if self.is_discovery:
            return "&"
        return " "

    def __bool__(self):
        return self.is_discovery

    def __nonzero__(self):
        return self.__bool__()


class TimeMPC(TimeString):
    """
    Override the TimeString class to convert from MPC format string to astropy.time.Time object.

    usage:

    from astropy.time.core import Time
    Time.FORMATS[TimeMPC.name] = TimeMPC

    t = Time('2000 01 01.00001', format='mpc', scale='utc')

    str(t) == '2000 01 01.000001'
    """

    name = 'mpc'
    subfmts = (('mpc', '%Y %m %d', "{year:4d} {mon:02d} {day:02d}.{fracday:s}"),)

    # ## need our own 'set_jds' function as the MPC Time string is not typical
    def set_jds(self, val1, val2):
        """

        Parse the time strings contained in val1 and set jd1, jd2

        :param val1: array of strings to parse into JD format
        :param val2: not used for string conversions but passed regardless
        """
        n_times = len(val1)  # val1,2 already checked to have same len
        iy = numpy.empty(n_times, dtype=numpy.intc)
        im = numpy.empty(n_times, dtype=numpy.intc)
        iday = numpy.empty(n_times, dtype=numpy.intc)
        ihr = numpy.empty(n_times, dtype=numpy.intc)
        imin = numpy.empty(n_times, dtype=numpy.intc)
        dsec = numpy.empty(n_times, dtype=numpy.double)

        # Select subformats based on current self.in_subfmt
        subfmts = self._select_subfmts(self.in_subfmt)

        for i, time_str in enumerate(val1):
            # Assume that anything following "." on the right side is a
            # floating fraction of a day.
            try:
                idot = time_str.rindex('.')
            except:
                fracday = 0.0
            else:
                time_str, fracday = time_str[:idot], time_str[idot:]
                fracday = float(fracday)

            for _, strptime_fmt, _ in subfmts:
                try:
                    tm = time.strptime(time_str, strptime_fmt)
                except ValueError:
                    pass
                else:
                    iy[i] = tm.tm_year
                    im[i] = tm.tm_mon
                    iday[i] = tm.tm_mday
                    ihr[i] = tm.tm_hour + int(24 * fracday)
                    imin[i] = tm.tm_min + int(60 * (24 * fracday - ihr[i]))
                    dsec[i] = tm.tm_sec + 60 * (60 * (24 * fracday - ihr[i]) - imin[i])
                    break
            else:
                raise ValueError("Time {0} does not match {1} format".format(time_str, self.name))

        self.jd1, self.jd2 = sofa_time.dtf_jd(self.scale.upper().encode('utf8'),
                                              iy, im, iday, ihr, imin, dsec)
        return

    def str_kwargs(self):
        """

        Generator that yields a dict of values corresponding to the

        calendar date and time for the internal JD values.

        Here we provide the additional 'fracday' element needed by 'mpc' format
        """
        iys, ims, ids, ihmsfs = sofa_time.jd_dtf(self.scale.upper()
                                                 .encode('utf8'),
                                                 6,
                                                 self.jd1, self.jd2)

        # Get the str_fmt element of the first allowed output subformat

        _, _, str_fmt = self._select_subfmts(self.out_subfmt)[0]

        yday = None
        has_yday = '{yday:' in str_fmt or False

        for iy, im, iday, ihmsf in itertools.izip(iys, ims, ids, ihmsfs):
            ihr, imin, isec, ifracsec = ihmsf
            if has_yday:
                yday = datetime(iy, im, iday).timetuple().tm_yday

            # MPC uses day fraction as time part of datetime
            fracday = (((((ifracsec / 1000000.0 + isec) / 60.0 + imin) / 60.0) + ihr) / 24.0) * (10 ** 6)
            fracday = '{0:06g}'.format(fracday)[0:self.precision]
            yield dict(year=int(iy), mon=int(im), day=int(iday), hour=int(ihr), min=int(imin), sec=int(isec),
                       fracsec=int(ifracsec), yday=yday, fracday=fracday)


Time.FORMATS[TimeMPC.name] = TimeMPC


def compute_precision(coord):
    """
    Returns the number of digits after the last '.' in a given number or string.

    """
    coord = str(coord).strip(' ')
    idx = coord.rfind('.')
    if idx < 0:
        return 0
    else:
        return len(coord) - idx - 1


def get_date(date_string):
    """
    Given an MPC formatted time string return a Time object.

    :rtype : Time
    :param date_string: a string in MPC date format
    """
    _date_precision = compute_precision(date_string)
    return Time(date_string, format='mpc', scale='utc', precision=_date_precision)


class Observation(object):
    """
    An observation of an object, nominally generated by reading an MPC formatted file.
    """

    def __init__(self,
                 null_observation=False,
                 provisional_name=None,
                 discovery=False,
                 note1=None,
                 note2=None,
                 date="2000 01 01.000001",
                 ra="00 00 00.000",
                 dec="+00 00 00.00",
                 mag=-1,
                 band='r',
                 observatory_code=568,
                 comment=None,
                 mag_err=-1,
                 xpos=None,
                 ypos=None,
                 frame=None,
                 plate_uncertainty=None,
                 astrometric_level=0):
        """

        :param provisional_name:
        :param discovery:
        :param note1:
        :param note2:
        :param date:
        :param ra:
        :param dec:
        :param mag:
        :param band:
        :param observatory_code:
        :param comment: A comment about this observation, not sent
        :param mag_err:
        :param xpos:
        :param ypos:
        :param frame:
        :param plate_uncertainty:
        :param null_observation:

        :type comment MPCComment
        """
        self._null_observation = False
        self.null_observation = null_observation
        self._provisional_name = ""
        self.provisional_name = provisional_name
        self._discovery = None
        self.discovery = discovery
        self._note1 = None
        self.note1 = note1
        self._note2 = None
        self.note2 = note2
        self._date = None
        self._date_precision = None
        self.date = date
        self._coordinate = None
        self.coordinate = (ra, dec)
        self._mag = None
        self._mag_err = None
        self._mag_precision = 1
        self._ra_precision = 3
        self._dec_precision = 2
        self.mag = mag
        self.mag_err = mag_err
        self._band = None
        self.band = band
        self._observatory_code = None
        self.observatory_code = observatory_code
        self._comment = None
        self.comment = OSSOSComment(version="O", frame=frame,
                                    source_name=provisional_name,
                                    photometry_note="",
                                    mpc_note=str(self.note1),
                                    x=xpos,
                                    y=ypos,
                                    plate_uncertainty=plate_uncertainty,
                                    astrometric_level=astrometric_level,
                                    magnitude=mag,
                                    mag_uncertainty=mag_err,
                                    comment=comment)

    def __eq__(self, other):
        return self.to_string() == other.to_string() 

    def __ne__(self, other):
        return self.to_string() != other.to_string()

    def __le__(self, other):
        return self.date <= other.date

    def __lt__(self, other):
        return self.date < other.date

    def __ge__(self, other):
        return self.date >= other.date

    def __gt__(self, other):
        return self.date > other.date


    @classmethod
    def from_string(cls, input_line):
        """
        Given an MPC formatted line, returns an MPC Observation object.
        :param mpc_line: a line in the one-line roving observer format
        """
        mpc_line = input_line.strip('\n')
        if len(mpc_line) > 0 and mpc_line[0] == '#':
            return MPCComment.from_string(mpc_line[1:])
        mpc_format = '1s11s1s1s1s17s12s12s9x5s1s6x3s'
        comment = mpc_line[81:]
        mpc_line = mpc_line[0:80]
        if len(mpc_line) != 80:
            return None
        obsrec = cls(*struct.unpack(mpc_format, mpc_line))
        obsrec.comment = MPCComment.from_string(comment)
        if isinstance(obsrec.comment, OSSOSComment) and obsrec.comment.source_name is None:
            obsrec.comment.source_name = obsrec.provisional_name
        # Check if there are TNOdb style flag lines.
        if isinstance(obsrec.comment, TNOdbComment):
            if obsrec.comment.flags[0] == '1':
                obsrec.discovery.is_discovery = True

        return obsrec

    def to_string(self):
        as_string = str(self)
        if self.comment is not None and str(self.comment) != "":
            as_string += " " + str(self.comment)
        return as_string

    def __str__(self):
        """
        Writes out data about accepted objects in the Minor Planet Center's 'Minor Planets'
        format as specified here:
        http://www.minorplanetcenter.net/iau/info/OpticalObs.html
        """
        # MOP/OSSOS allows the provisional name to take up the full space allocated to the MinorPlanetNumber AND
        # the provisional name.

        if len(self.provisional_name) > 7:
            padding = ""
        else:
            padding = " " * 4
        ## padding = " " * min(4, 11 - len(self.provisional_name))
        mpc_str = "%-12s" % (str(self.null_observation) + padding + self.provisional_name)

        mpc_str += str(self.discovery)
        mpc_str += '{0:1s}{1:1s}'.format(str(self.note1), str(self.note2))
        mpc_str += '{0:<17s}'.format(str(self.date))
        mpc_str += '{0:<12s}{1:<12s}'.format(str(self.ra), str(self.dec))
        mpc_str += 9 * " "
        mag_format = '{0:<5.' + str(self._mag_precision) + 'f}{1:1s}'
        mag_str = (self.mag is None and 6 * " ") or mag_format.format(self.mag, self.band)
        if len(mag_str) != 6:
            raise MPCFieldFormatError("mag",
                                      "length of mag string should be exactly 6 characters, got->",
                                      mag_str)
        mpc_str += mag_str
        mpc_str += 6 * " "
        mpc_str += "%3s" % self.observatory_code
        return mpc_str

    def to_tnodb(self):
        """
        provide string representation of observation in a format used for OSSOS database input.
        """

        # O indicates OSSOS survey
        if not isinstance(self.comment, OSSOSComment):
            logging.warn("Non OSSOS comment:{}".format(self.comment))

        comment_line = "#"+str(self.comment).rstrip('\n')

        if self.mag == -1:  # write no mag and no filter for where photometry couldn't be measured
            self.mag = None
        else:
            # set mag precision back to 0.1 mags regardless of how good it actually is
            self._mag_precision = 1

        # set the null observation character to the tnodb value
        self.null_observation.null_observation_character = "-"
        mpc_observation = str(self)

        return comment_line + '\n' + mpc_observation

    def to_mpc(self):
        self.null_observation.null_observation_character = "#"
        return str(self)

    @property
    def null_observation(self):
        return self._null_observation

    @null_observation.setter
    def null_observation(self, null_observation=False):
        """
        :param null_observation: is this a null observation marker True/False
        """
        self._null_observation = NullObservation(null_observation)

    @property
    def provisional_name(self):
        return self._provisional_name

    @provisional_name.setter
    def provisional_name(self, provisional_name=None):
        if provisional_name is None:
            provisional_name = " " * 7
        else:
            provisional_name = provisional_name.strip()
            # if not provisional_name[0].isalpha():
            # logging.warning("Provisional Name should not be a number: {}".format(provisional_name))
            # if not len(provisional_name) <= 7:
            #     logging.warning("Provisional Name too long {}".format(provisional_name))
        self._provisional_name = provisional_name

    @property
    def discovery(self):
        """
        Is this a discovery observation?

        :return True/False
        """
        return self._discovery

    @discovery.setter
    def discovery(self, is_discovery):
        """

        :type is_discovery: bool
        :param is_discovery: indicates if observation was a discovery
        """
        self._discovery = Discovery(is_discovery=is_discovery)

    @property
    def note1(self):
        return self._note1

    @note1.setter
    def note1(self, note1):
        self._note1 = MPCNote(code=note1, note_type="Note1")

    @property
    def note2(self):
        return self._note2

    @note2.setter
    def note2(self, code):
        self._note2 = MPCNote(code=code, note_type="Note2")

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date_str):
        self._date_precision = compute_precision(date_str)
        try:
            self._date = Time(date_str, format='mpc', scale='utc', precision=self._date_precision)
        except:
            raise MPCFieldFormatError("Observation Date",
                                      "does not match expected format",
                                      date_str)

    @property
    def ra(self):
        return self.coordinate.ra.format(unit=units.hour, decimal=False,
                                         sep=" ", precision=self._ra_precision, alwayssign=False,
                                         pad=True)

    @property
    def dec(self):
        return self.coordinate.dec.format(unit=units.degree, decimal=False,
                                          sep=" ", precision=self._dec_precision, alwayssign=True,
                                          pad=True)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        if comment is None:
            self._comment = ""
        else:
            self._comment = comment

    @property
    def coordinate(self):
        return self._coordinate

    @coordinate.setter
    def coordinate(self, coord_pair):
        """

        :param coord_pair: RA/DEC pair [as a tuple or single string]
        """

        if type(coord_pair) in [list, tuple] and len(coord_pair) == 2:
            val1 = coord_pair[0]
            val2 = coord_pair[1]
        else:
            raise MPCFieldFormatError("RA/DEC",
                                      "Expected a pair of coordinates got: ",
                                      coord_pair)

        self._ra_precision = 3
        self._dec_precision = 2
        try:
            ra = float(val1)
            dec = float(val2)
            self._coordinate = ICRSCoordinates(ra, dec, unit=(units.degree, units.degree))
        except:
            try:
                self._ra_precision = compute_precision(val1)
                self._dec_precision = compute_precision(val2)
                self._coordinate = ICRSCoordinates(val1, val2, unit=(units.hour, units.degree))
            except Exception as e:
                sys.stderr.write(str(e)+"\n")
                raise MPCFieldFormatError("coord_pair",
                                          "must be [ra_deg, dec_deg] or HH MM SS.S[+-]dd mm ss.ss",
                                          coord_pair)

    @property
    def mag(self):
        return self._mag

    @mag.setter
    def mag(self, mag):
        if mag is None or len(str(str(mag).strip(' '))) == 0 or float(mag) < 0:
            self._mag_precision = 0
            self._mag = None
        else:
            self._mag = float(mag)
            self._mag_precision = min(1, compute_precision(str(mag)))

    @property
    def mag_err(self):
        return self._mag_err

    @mag_err.setter
    def mag_err(self, mag_err):
        if mag_err is None or len(str(mag_err).strip('')) == 0 or self.mag is None:
            self._mag_err = None
        else:
            self._mag_err = mag_err


    @property
    def band(self):
        return self._band

    @band.setter
    def band(self, band):
        band = str(band.strip(' '))
        self._band = (len(band) > 0 and str(band)[0]) or None

    @property
    def observatory_code(self):
        return self._observatory_code

    @observatory_code.setter
    def observatory_code(self, observatory_code):
        observatory_code = str(observatory_code)
        if not len(observatory_code) <= 3:
            raise MPCFieldFormatError("Observatory code",
                                      "must be 3 characters or less",
                                      observatory_code)
        self._observatory_code = str(observatory_code)


class OSSOSComment(object):
    """
    Parses an OSSOS observation's metadata into a format that can be stored in the 
    an Observation.comment and written out in the same MPC line.

    Specification: '1s1x10s1x11s1x2s1x7s1x7s1x4s1x1s1x5s1x4s1x'
    """

    def __init__(self, version, frame, source_name, photometry_note, mpc_note, x, y,
                 plate_uncertainty=0.2,
                 astrometric_level=0,
                 magnitude=None,
                 mag_uncertainty=None,
                 comment=None):

        self.version = version
        self.frame = frame
        self.source_name = source_name
        self._photometry_note = None
        self.photometry_note = photometry_note
        self.mpc_note = mpc_note
        self._x = None
        self.x = x
        self._y = None
        self.y = y
        self._mag = None
        self.mag = magnitude
        self._mag_uncertainty = None
        self.mag_uncertainty = mag_uncertainty
        self._plate_uncertainty = None
        self.plate_uncertainty = plate_uncertainty
        self._astrometric_level = 0
        self.astrometric_level = astrometric_level
        self._comment = ""
        self.comment = comment
        self.flags = None

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __le__(self, other):
        raise NotImplemented

    def __ge__(self, other):
        raise NotImplemented

    @classmethod
    def from_string(cls, comment):
        """
        Build an MPC Comment from a string.
        """
        if comment is None or len(comment) == 0:
            return str("")
        if comment[0] == "#":
            comment = comment[1:]
        values = comment.split('%')
        comment_string = ""
        if len(values) > 1:
            comment_string = values[1].lstrip(' ')
        # O 1631355p21 O13AE2O     Z  1632.20 1102.70 0.21 3 ----- ---- % Apcor failure.
        ossos_comment_format = '1s1x10s1x11s1x1s1s1x7s1x7s1x4s1x1s1x5s1x4s1x'
        try:
            retval = cls(*struct.unpack(ossos_comment_format, values[0]))
            retval.comment = values[1]
            return retval
        except Exception as e:
            logging.debug(str(e))
            logging.debug("OSSOS Fixed Format Failed.")
            logging.debug(comment)
            logging.debug("Trying space separated version")

        values = values[0].split()
        try:
            if values[0] != 'O' or len(values) < 5:
                # this is NOT and OSSOS style comment string
                raise ValueError("Can't parse non-OSSOS style comment: {}".format(comment))
            # first build a comment based on the required fields.
            retval = cls(version="O",
                         frame=values[1],
                         source_name=values[2],
                         photometry_note=values[3][0],
                         mpc_note=values[3][1:],
                         x=values[4],
                         y=values[5],
                         comment=comment_string)
        except Exception as e:
            logging.error(str(e))
            raise e


        retval.version = values[0]
        logging.debug("length of values: {}".format(len(values)))
        logging.debug("Values: {}".format(str(values)))
        # the format of the last section evolved during the survey, but the following flags should handle this.
        if len(values) == 7:
            retval.plate_uncertainty = values[6]
        elif len(values) == 8:
            retval.plate_uncertainty = values[6]
            retval.astrometric_level = values[7]
        elif len(values) == 9:  # This is the old format where mag was in-between X/Y and uncertainty in X/Y
            retval.mag = values[6]
            retval.mag_uncertainty = values[7]
            retval.plate_uncertainty = values[8]
        elif len(values) == 10:  # if there are 9 values then the new astrometric level value is set.
            retval.plate_uncertainty = values[8]
            retval.astrometric_level = values[9]
            logging.debug('here now')
            retval.mag = values[6]
            retval.mag_uncertainty = values[7]
        logging.debug("DONE.")
        return retval


    @property
    def mag(self):
        return self._mag

    @mag.setter
    def mag(self, mag):
        try:
            self._mag = float(mag)
            self.photometry_note = "Y"
            if not 15 < self._mag < 30:
                raise ValueError("Magnitude out of reasonable range:  15 < mag < 30")
        except:
            self.photometry_note = "Z"
            self._mag = None

    @property
    def mag_uncertainty(self):
        return self._mag_uncertainty

    @mag_uncertainty.setter
    def mag_uncertainty(self, mag_uncertainty):
        try:
            self._mag_uncertainty = float(mag_uncertainty)
            if not 0 < self._mag_uncertainty < 1.0:
                raise ValueError("mag uncertainty must be in range 0 to 1")
        except Exception as e:
            logging.debug("Failed trying to convert mag_uncertainty ({}) to float. Using default.".format(mag_uncertainty))
            logging.debug(str(e))
            if str(self.mag).isdigit():
                self.photometry_note = "L"
            else:
                self.photometry_note = "Z"
            self._mag_uncertainty = None

    @property
    def photometry_note(self):
        return self._photometry_note

    @property
    def astrometric_level(self):
        return self._astrometric_level

    @astrometric_level.setter
    def astrometric_level(self, astrometric_level):
        astrometric_level = int(astrometric_level)
        if not -1 < astrometric_level < 10:
            raise ValueError("Astrometric level must be integer between 0 and 9.")
        self._astrometric_level = astrometric_level

    @photometry_note.setter
    def photometry_note(self, photometry_note):
        self._photometry_note = str(photometry_note)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        try:
            self._x = float(x)
        except:
            self._x = None

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        try:
            self._y = float(y)
        except:
            self._y = None

    @property
    def plate_uncertainty(self):
        return self._plate_uncertainty

    @plate_uncertainty.setter
    def plate_uncertainty(self, plate_uncertainty):
        try:
            self._plate_uncertainty = float(plate_uncertainty)
        except:
            self._plate_uncertainty = 0.2
        if not 0 < self._plate_uncertainty < 100:
            raise ValueError("Plate uncertainty must be between 0 and 100. (in arc-seconds)")

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        if comment is not None:
            try:
                self._comment = str(comment.strip())
            except:
                self._comment = ''
        else:
            self._comment = ''

    def to_str(self, frmt, value, default="", sep=" "):
        try:
            if value is None:
                raise ValueError("Don't print None.")
            return sep+frmt.format(value)
        except:
            return sep+default

    def __str__(self):
        """
        Format comment as required for storing OSSOS metadata
        odonum p ccd object_name MPCnotes X Y mag mag_uncertainty plate_uncertainty % comment
        """
        # The astrometric uncertainty should be set to higher when hand measurements are made.
        if self.version == "T":
            return self.comment

        if self.version == "L":
            return "{:1s} {:10s} {}".format(self.version, self.frame, self.comment)

        comm = '{:1s}'.format(self.version)
        comm += self.to_str("{:>10.10s}", self.frame, "-"*10)
        comm += self.to_str("{:<11.11s}", self.source_name, "-"*11)
        comm += self.to_str("{:2.2s}", self.photometry_note+self.mpc_note, "--")
        comm += self.to_str("{:>7.2f}", self.x, "-"*7)
        comm += self.to_str("{:>7.2f}", self.y, "-"*7)
        comm += self.to_str('{:4.2f}', self.plate_uncertainty, "-"*4)
        comm += self.to_str('{:1d}', self.astrometric_level, "-")
        comm += self.to_str('{:5.2f}', self.mag, "-"*5)
        comm += self.to_str('{:4.2f}', self.mag_uncertainty, "-"*4)
        comm += ' % {}'.format(self.comment)

        return comm


class MPCWriter(object):
    """
    Writes out data about accepted objects in the Minor Planet Center's
    format as specified here:
    http://www.minorplanetcenter.net/iau/info/OpticalObs.html

    Note that we assume objects fall under the Minor Planet category.

    Format reproduced below for convenience:

        Columns     Format   Use
        1 -  5        A5     Minor planet number
        6 - 12        A7     Provisional or temporary designation
        13            A1     Discovery asterisk
        14            A1     Note 1
        15            A1     Note 2
        16 - 32      A17     Date of observation
        33 - 44      A12     Observed RA (J2000.0)
        45 - 56      A12     Observed Decl. (J2000.0)
        57 - 65       9X     Must be blank
        66 - 71    F5.2,A1   Observed magnitude and band
                               (or nuclear/total flag for comets)
        72 - 77       6X     Must be blank
        78 - 80       A3     Observatory code
    """

    def __init__(self, file_handle, auto_flush=True, include_comments=True,
                 auto_discovery=True, formatter=None):
        self.filehandle = file_handle
        self.auto_flush = auto_flush
        self.include_comments = include_comments

        # Holds observations that have not yet been flushed
        self.buffer = {}
        self._written_mpc_observations = []

        self.auto_discovery = auto_discovery
        self._discovery_written = False
        if formatter is None:
            if self.include_comments:
                self.formatter = Observation.to_string
            else:
                self.formatter = Observation.__str__
        else:
            self.formatter = formatter

    def get_filename(self):
        return self.filehandle.name

    def write(self, mpc_observation):
        """
        Writes a single entry in the Minor Planet Center's format.
        :param mpc_observation:
        """
        assert isinstance(mpc_observation, Observation)
        key = mpc_observation.date.mjd
        self.buffer[key] = mpc_observation

        if self.auto_flush:
            self.flush()

    def flush(self):
        for obs in self.get_chronological_buffered_observations():
            self._flush_observation(obs)

        self.filehandle.flush()

    def _flush_observation(self, obs):
        isinstance(obs, Observation)
        if (self.auto_discovery and
                not obs.null_observation and
                not self._discovery_written):
            obs.discovery = True

        if obs.discovery:
            if self._discovery_written:
                obs.discovery.is_initial_discovery = False
            else:
                self._discovery_written = True

        if obs.date.jd not in self._written_mpc_observations:
            self._written_mpc_observations.append(obs.date.jd)
            line = self.formatter(obs)
            self.filehandle.write(line + "\n")

    def close(self):
        self.filehandle.close()

    def get_chronological_buffered_observations(self):
        jds = self.buffer.keys()
        jds.sort()
        sorted_obs = []
        for jd in jds:
            sorted_obs.append(self.buffer[jd])
        return sorted_obs


def make_tnodb_header(observations, observatory_code=None, observers=DEFAULT_OBSERVERS,
                      telescope=DEFAULT_TELESCOPE, astrometric_network=DEFAULT_ASTROMETRIC_NETWORK):
    """
    Write a header appropriate for a tnodb style of file.
    """
    observatory_code = observatory_code is None and observations[0].observatory_code or observatory_code

    odates = [obs.date for obs in observations]
    mindate = min(odates).iso.replace('-', '')[0:8]
    maxdate = max(odates).iso.replace('-', '')[0:8]

    header = "COD {}\n".format(observatory_code)

    sep = ""
    header += "OBS "
    for observer in observers[:-1]:
        header += "{}{}".format(sep, observer)
        sep = ", "
    if len(observers) > 1:
        header += " and {}".format(observers[-1])

    header += "\n"
    header += "TEL {}\n".format(telescope)
    header += "NET {}\n".format(astrometric_network)
    header += "{:s} {:s}\n".format('STD', mindate)
    header += "{:s} {:s}\n".format('END', maxdate)

    return header


class MPCReader(object):
    """
    A class to read in MPC files.

    Can be initialized with a filename, will then initialize the mpc_observations attribute to hold the observations.
    """

    def __init__(self, filename=None, replace_provisional=None, provisional_name=None):
        self.replace_provisional = replace_provisional
        self._provisional_name = provisional_name
        if filename is not None:
            self.filename = filename
            self.mpc_observations = self.read(filename)

    def read(self, filename):
        """
        Read  MPC records from filename:

        :param filename: filename of file like object.
        :rtype : numpy.ndarray
        """

        self.filename = filename
        # can be a file like objects,
        if isinstance(filename, basestring):
            filehandle = storage.open_vos_or_local(filename, "rb")
        else:
            filehandle = filename

        filestr = filehandle.read()
        filehandle.close()
        input_mpc_lines = filestr.split('\n')
        mpc_observations = []
        next_comment = None
        for line in input_mpc_lines:
            try:
                mpc_observation = Observation.from_string(line)
                if isinstance(mpc_observation, OSSOSComment):
                    next_comment = mpc_observation
                    continue
                if isinstance(mpc_observation, Observation):
                    if next_comment is not None:
                        mpc_observation.comment = next_comment
                        next_comment = None

                    if self.replace_provisional is not None:  # then it has an OSSOS designation: set that in preference
                        mpc_observation.provisional_name = self.provisional_name
                    mpc_observations.append(mpc_observation)
            except:
                continue
        return numpy.array(mpc_observations)

    @property
    def provisional_name(self):
        """
        Determine the provisional name based on the file being accessed.
        :return: str
        """
        if self._provisional_name is not None:
            return self._provisional_name
        if isinstance(self.filename, basestring):
            self._provisional_name = self.filename.rstrip('.ast')
        elif hasattr(self.filename, 'name'):
            self._provisional_name = self.filename.name
        elif hasattr(self.filename, 'filename'):
            self._provisional_name = self.filename.filename
        elif hasattr(self.filename, '__class__'):
            self._provisional_name = str(self.filename.__class__)
        else:
            self._provisional_name = str(type(self.filename))
        self._provisional_name = os.path.basename(self._provisional_name)
        return self._provisional_name


class Index(object):
    """
    MOP/OSSOS name mapping index.
    """
    MAX_NAME_LENGTH = 10

    def __init__(self, idx_filename):
        self.names = {}
        self.index = {}
        with open(idx_filename, 'r') as idx_handle:
            for line in idx_handle.readlines():
                master_name = line[0:Index.MAX_NAME_LENGTH]
                master_name = master_name.strip()
                self.names[master_name] = master_name
                self.index[master_name] = [master_name]
                for i in range(Index.MAX_NAME_LENGTH, len(line), Index.MAX_NAME_LENGTH):
                    this_name = line[i:i + Index.MAX_NAME_LENGTH].strip()
                    self.index[master_name].append(this_name)
                    self.names[this_name] = master_name

    def __str__(self):
        result = ""
        for name in self.index:
            result += "{0:<{1}s}".format(name, Index.MAX_NAME_LENGTH)
            for alias in self.get_aliases(name):
                result += "{0:<{1}s}".format(alias, Index.MAX_NAME_LENGTH)
            result += "\n"
        return result

    def get_aliases(self, name):
        """
        get all names associated with a given name.
        :rtype : list
        :param name: object to get alias names of.
        """
        if name not in self.names:
            return name
        return self.index[self.names[name]]

    def is_same(self, name1, name2):
        """
        Do name1 and name2 refer to the same object?

        :param name1: name of object 1
        :param name2: name of object 2
        :return: Bool
        """
        return name2 in self.get_aliases(name1)


class MPCConverter(object):
    """
    Converts an MPC formatted file to a TNOdb one.
    :param mpc_file The input filename, of MPC lines.
    :param output   if required; else will use root of provided MPC file.

    batch_convert is factory method that will write out a series of input files given an input path.
    """

    def __init__(self, mpc_file, output=None):

        if output is None:
            output = mpc_file.rpartition('.')[0] + '.tnodb'

        self.mpc_file = mpc_file
        self.outfile = open(output, 'w')
        self.write_header = True

    def convert(self):
        with open(self.mpc_file, 'r') as infile:
            observations = []
            for line in infile.readlines():
                obs = Observation().from_string(line)
                observations.append(obs)

            if self.write_header:
                self.outfile.write(make_tnodb_header(observations))
                self.write_header = False

            for obs in observations:
                self.outfile.write(obs.to_tnodb() + '\n')

    @classmethod
    def batch_convert(cls, path):
        for fn in os.listdir(path):
            if fn.endswith('.mpc') or fn.endswith('.track') or fn.endswith('.checkup') or fn.endswith('.nailing'):
                cls(path + fn).convert()



class CFEPSComment(OSSOSComment):
    """
    This holds the old-style comments that come for CFEPS style entries.
    """
    def __init__(self, frame, comment):

        if "measured inside confirm @" in comment:
            values = comment.split('@')[1].split()
            x = values[0]
            y = values[1]
        else:
            x = ""
            y = ""
        source_name = None
        mpc_note = " "
        super(CFEPSComment, self).__init__("O", frame, source_name, " ", mpc_note, x, y, comment=comment)
        self.version = "L"

    @classmethod
    def from_string(cls, comment):
        """
        Build a comment from a CFEPS style comment string.
        """
        values = comment.split()
        if values[0] != "L" or len(values) < 2:
            raise ValueError("Not a CFEPS style comment: {}".format(comment))
        frame = values[1]
        comment = " ".join(values[2:])
        return cls(frame, comment)


class TNOdbComment(OSSOSComment):
    """
    This holds a TNOdb style comment line which contains flags.

    A TNOdb style comment consists of three space seperated fields that are used by the tnodb followed by a
    comment string that is either in the CFEPS or OSSOS format.
    """
    def __init__(self, index, date, flags, **kwargs):

        super(TNOdbComment, self).__init__(**kwargs)
        self.index = index
        self.date = date
        self.flags = flags

    @classmethod
    def from_string(cls, line):
        if len(line) < 56:
            raise ValueError("Line too short, not a valid TNOdb comment string: {}".format(line))
        index = line[0:14].strip()
        if not re.match(r'\d{8}_\S{3}_\S', index):
            raise ValueError("No valid flags, not a valid TNOdb comment string: {}".format(line))

        date = line[15:23].strip()
        flags = line[24:34].strip()
        comment = line[56:].strip()

        comment_object = None
        # try build a comment object based on the TNOdb comment string
        if len(comment) > 0:
            for func in [OSSOSComment.from_string,
                         CFEPSComment.from_string]:
                try:
                    comment_object = func(comment)
                except ValueError as verr:
                    logging.debug(verr)
                    continue
                break

        if isinstance(comment_object, OSSOSComment):
            retval = cls(index,
                         date,
                         flags,
                         version=comment_object.version,
                         frame=comment_object.frame,
                         source_name=comment_object.source_name,
                         mpc_note=comment_object.mpc_note,
                         x=comment_object.x,
                         y=comment_object.y,
                         magnitude=comment_object.mag,
                         mag_uncertainty=comment_object.mag_uncertainty,
                         photometry_note=comment_object.photometry_note,
                         plate_uncertainty=comment_object.plate_uncertainty,
                         astrometric_level=comment_object.astrometric_level,
                         comment=comment_object.comment)
            return retval
        else:
            retval = cls(index,
                         date,
                         flags,
                         version="T",
                         frame=" ",
                         source_name="",
                         photometry_note=" ",
                         mpc_note=" ",
                         x=" ",
                         y=" ",
                         comment=comment)
            return retval

    def to_string(self):
        comm = "{} {} {}".format(self.index, self.date, self.flags)
        # add 22 spaces that are currently padding in TNOdb style records.
        comm += " "*22
        comm += str(self)
        return comm

class RealOSSOSComment(OSSOSComment):

    @classmethod
    def from_string(cls, comment):
        if comment.strip()[0] != "O":
            comment = "O "+comment
        return super(RealOSSOSComment, cls).from_string(comment)

class MPCComment(OSSOSComment):
    """
    A generic class for all comment strings.. try and figure out which one to use.
    """

    @classmethod
    def from_string(cls, line):
        comment = line
        logging.debug('Here is the comment. ' + comment)
        for func in [TNOdbComment.from_string,
                     OSSOSComment.from_string,
                     RealOSSOSComment.from_string,
                     CFEPSComment.from_string,
                     str]:
            try:
                comment = func(line)
            except ValueError as verr:
                logging.debug(str(func))
                logging.debug(str(verr))
                continue
            break
        return comment

