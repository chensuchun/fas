# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2008 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
#            Toshio Kuratomi <tkuratom@redhat.com>
#
'''Collection of validators for parameters coming to FAS URLs.'''

# Validators don't need an __init__ method (W0232)
# Validators are following an API specification so need methods that otherwise
#   would be functions (R0201)
# Validators will usu. only have two methods (R0903)
# pylint: disable-msg=W0232,R0201,R0903

# Disabled inline for specific cases:
# Validators will have a variable "state" that is very seldom used (W0163)
# Validator methods don't really need docstrings since the validator docstring
#   pretty much covers it (C0111)

import re

from turbogears import validators, config
from sqlalchemy.exceptions import InvalidRequestError
from fas.util import available_languages

from fas.model import People, Groups

### HACK: TurboGears/FormEncode requires that we use a dummy _ function for
# error messages.
# http://docs.turbogears.org/1.0/Internationalization#id13
def _(s):
    return s

class KnownGroup(validators.FancyValidator):
    '''Make sure that a group already exists'''
    messages = {'no_group': _("The group '%(group)s' does not exist.")}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # Just make sure the group already exists
            # pylint: disable-msg=W0612
            group = Groups.by_name(value)
        except InvalidRequestError:
            raise validators.Invalid(self.message('no_group', state, group=value),
                    value, state)

class UnknownGroup(validators.FancyValidator):
    '''Make sure that a group doesn't already exist'''
    messages = {'exists': _("The group '%(group)s' already exists.")}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # Just make sure the group doesn't already exist
            # pylint: disable-msg=W0612
            group = Groups.by_name(value)
        except InvalidRequestError:
            pass
        else:
            raise validators.Invalid(self.message('exists', state, group=value),
                    value, state)

class ValidGroupType(validators.FancyValidator):
    '''Make sure that a group type is valid'''
    messages = {'invalid_type': _('Invalid group type: %(type)s.')}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if value not in ('system', 'bugzilla', 'cla', 'cvs', 'bzr', 'git', \
            'hg', 'mtn', 'svn', 'shell', 'torrent', 'tracker', \
            'tracking', 'user'):
            raise validators.Invalid(self.message('invalid_type', state, type=value),
                    value, state)

class ValidRoleSort(validators.FancyValidator):
    '''Make sure that a role sort key is valid'''
    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()
    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if value not in ('username', 'sponsor', 'role_type', 'role_status', \
            'creation', 'approval'):
            raise validators.Invalid(_("Invalid sort key.") % value,
                    value, state)

class KnownUser(validators.FancyValidator):
    '''Make sure that a user already exists'''
    messages = {'no_user': _("'%(user)s' does not exist.")}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # just prove that we can retrieve a person for the username
            # pylint: disable-msg=W0612
            people = People.by_username(value)
        except InvalidRequestError:
            raise validators.Invalid(self.message('no_user', state, user=value),
                    value, state)

class UnknownUser(validators.FancyValidator):
    '''Make sure that a user doesn't already exist'''
    messages = {'create_error': _("Error: Could not create - '%(user)s'"),
            'exists': _("'%(user)s' already exists.")}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        try:
            # just prove that we *cannot* retrieve a person for the username
            # pylint: disable-msg=W0612
            people = People.by_username(value)
        except InvalidRequestError:
            return
        except:
            raise validators.Invalid(self.message('create_error', state, user=value),
                    value, state)

        raise validators.Invalid(self.message('exists', state, user=value),
                value, state)

class NonFedoraEmail(validators.FancyValidator):
    '''Make sure that an email address is not @fedoraproject.org'''
    messages = {'no_loop': _('To prevent email loops, your email address'
        ' cannot be @fedoraproject.org.')}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if value.endswith('@fedoraproject.org'):
            raise validators.Invalid(self.message('no_loop', state), value, state)

class ValidSSHKey(validators.FancyValidator):
    ''' Make sure the ssh key uploaded is valid '''
    messages = {'invalid_key': _('Error - Not a valid RSA SSH key: %(key)s')}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        #return value.file.read().decode('utf-8')
        return value

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
#        value = value.file.read()
        keylines = value.split('\n')
        for keyline in keylines:
            if not keyline:
                continue
            keyline = keyline.strip()
            validline = re.match('^(rsa|ssh-rsa) [ \t]*[^ \t]+.*$', keyline)
            if not validline:
                raise validators.Invalid(self.message('invalid_key', state,
                        key=keyline), value, state)

class ValidUsername(validators.FancyValidator):
    '''Make sure that a username isn't blacklisted'''
    username_regex = re.compile(r'^[a-z][a-z0-9]+$')
    username_blacklist = config.get('username_blacklist').split(',')

    messages = {'invalid_username': _("'%(username)s' is an illegal username.  "
        "A valid username must only contain lowercase alphanumeric characters, "
        "and must start with a letter."),
        'blacklist': _("'%(username)s' is an blacklisted username.  Please "
        "choose a different one.")}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if not self.username_regex.match(value):
            raise validators.Invalid(self.message('invalid_username', state,
                username=value), value, state)
        if value in self.username_blacklist:
            raise validators.Invalid(self.message('blacklist', state, username=value),
                    value, state)

class ValidLanguage(validators.FancyValidator):
    '''Make sure that a username isn't blacklisted'''
    messages = {'not_available': _("The language '%(lang)s' is not available.")}

    def _to_python(self, value, state):
        # pylint: disable-msg=C0111,W0613
        return value.strip()

    def validate_python(self, value, state):
        # pylint: disable-msg=C0111
        if value not in available_languages():
            raise validators.Invalid(self.message('not_available', state, lang=value),
                    value, state)

class PasswordStrength(validators.UnicodeString):
    '''Make sure that a password meets our strength requirements'''

    messages = {'strength': _('Passwords must meet certain strength requirements.  If they have a mix of symbols, upper and lowercase letters, and digits they must be at least 9 characters.  If they have a mix of upper and lowercase letters and digits they must be at least 10 characters.  If they have lowercase letters and digits, they must be at least 12 characters.  Letters alone means they need 20 or more characters.'),
            'xkcd': _('Malicious hackers read xkcd, you know')}

    def validate_python(self, value, state):
        # http://xkcd.com/936/
        if value.lower() in (u'correct horse battery staple',
                u'correcthorsebatterystaple', u'tr0ub4dor&3'):
            raise validators.Invalid(self.message('xkcd', state), value, state)

        length = len(value)
        if length >= 20:
            return
        if length < 9:
            raise validators.Invalid(self.message('strength', state),
                    value, state)

        lower = upper = digit = space = symbol = False

        for c in value:
            if c.isalpha():
                if c.islower():
                    lower = True
                else:
                    upper = True
            elif c.isdigit():
                digit = True
            elif c.isspace():
                space = True
            else:
                symbol = True

        if upper and lower and digit and symbol:
            if length >= 9:
                return
        elif upper and lower and (digit or symbol):
            if length >= 10:
                return
        elif (lower or upper) and (digit or symbol):
            if length >= 12:
                return
        raise validators.Invalid(self.message('strength', state), value, state)


class ValidHumanWithOverride(validators.FormValidator):
    '''Perform some simple heuristics on the person's human name.

    We need a legally valid name.  We need to try to screen out names that are
    possibly bad here.  This should be used with an override switch that lets
    a user tell us that his legal name really matches the heuristics we
    establish.

    Present heuristics are that the name must be multiple words and that the
    last name cannot be a single letter or a letter followed by a period.

    This validator is meant to be used as a chained validator with a text
    input field for the human name and a boolean checkbox field for the
    override.  Here's a n example of using it from within
    a :class:`formencode.Schema`::

        class TestSchema(Schema):
            human_name = validators.UnicodeString(not_empty=True)
            name_override = validators.StringBool(if_missing=False)
            chained_validators = [ValidHumanWithOverride('human_name', 'name_override')]
    '''

    messages = {'noname': _('You must enter your legal name'),
            'lastfirst': _('You must include both your last name and first name.  If your name really only consists of a single letter, you may check the override checkbox to submit this name.'),
            'initial': _('You must include the full form of your names, not just initials.  If your fullname really has one letter portions, you may check the override checkbox to submit this name.')}

    def __init__(self, name_field, override_field):
        super(validators.FormValidator, self).__init__()
        self.name_field = name_field
        self.override = override_field

    def validate_python(self, values, state):
        # Check that a name was entered
        name = values.get(self.name_field)
        if not name:
            raise validators.Invalid(self.message('noname', state), values, state)

        # If override is set, then we skip the rest of testing
        if values.get(self.override, False):
            return

        # Check that the name is more than one word
        split_name = name.split(u' ')
        if len(split_name) < 2:
            raise validators.Invalid(self.message('lastfirst', state), values, state)

        # Check for initials
        for name_part in split_name:
            if len(name_part.rstrip(u'.')) <= 1:
                raise validators.Invalid(self.message('initial', state), values, state)

