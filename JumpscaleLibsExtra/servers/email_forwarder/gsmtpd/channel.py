#!/usr/bin/env python
# encoding: utf-8

import logging

logger = logging.getLogger(__name__)
from gevent import monkey, socket, ssl

import errno
from asynchat import find_prefix_at_end

NEWLINE = "\n"
EMPTYSTRING = ""
COMMASPACE = ", "


class SMTPChannel(object):
    """
    Port from stdlib smtpd used by Gevent
    """

    COMMAND = 0
    DATA = 1

    def __init__(self, server, conn, addr, data_size_limit=1024000):
        self.server = server
        self.conn = conn
        self.addr = addr
        self.line = []
        self.state = self.COMMAND
        self.seen_greeting = 0
        self.mailfrom = None
        self.rcpttos = []
        self.data = ""
        self.fqdn = socket.getfqdn()
        self.ac_in_buffer_size = 4096

        self.ac_in_buffer = ""
        self.closed = False
        self.data_size_limit = data_size_limit  # in byte
        self.current_size = 0
        self.tls = False
        try:
            self.peer = conn.getpeername()
        except socket.error as err:
            # a race condition  may occur if the other end is closing
            # before we can get the peername
            logger.error(err)
            self.conn.close()
            if err[0] != errno.ENOTCONN:
                raise
            return
        self.push("220 %s GSMTPD at your service" % self.fqdn)
        self.terminator = "\r\n"
        logger.debug("SMTP channel initialized")

    # Overrides base class for convenience
    def push(self, msg):
        logger.debug("PUSH %s" % msg)
        msg = msg + "\r\n"
        self.conn.sendall(msg.encode("utf-8"))

    # Implementation of base class abstract method
    def collect_incoming_data(self, data):
        self.line.append(data)
        self.current_size += len(data)
        if self.current_size > self.data_size_limit:
            self.push("452 Command has been aborted because mail too big")
            self.close_when_done()

    # Implementation of base class abstract method
    def found_terminator(self):
        line = EMPTYSTRING.join(self.line)
        self.line = []
        if self.state == self.COMMAND:
            if not line:
                self.push("500 Error: bad syntax")
                return
            method = None
            i = line.find(" ")
            if i < 0:
                command = line.upper().strip()
                arg = None
            else:
                command = line[:i].upper()
                arg = line[i + 1 :].strip()
            method = getattr(self, "smtp_" + command, None)
            logger.debug("%s:%s", command, arg)
            if not method:
                self.push('502 Error: command "%s" not implemented' % command)
                return
            method(arg)
            return
        else:
            if self.state != self.DATA:
                self.push("451 Internal confusion")
                return
            # Remove extraneous carriage returns and de-transparency according
            # to RFC 821, Section 4.5.2.
            data = []
            for text in line.split("\r\n"):
                if text and text[0] == ".":
                    data.append(text[1:])
                else:
                    data.append(text)
            self.data = NEWLINE.join(data)
            status = self.server.process_message(self.peer, self.mailfrom, self.rcpttos, self.data)
            self.rcpttos = []
            self.mailfrom = None
            self.state = self.COMMAND
            self.terminator = "\r\n"
            if not status:
                self.push("250 Ok")
            else:
                self.push(status)

    # SMTP and ESMTP commands
    def smtp_HELO(self, arg):
        if not arg:
            self.push("501 Syntax: HELO hostname")
            return
        if self.seen_greeting:
            self.push("503 Duplicate HELO/EHLO")
        else:
            self.seen_greeting = arg
            self.push("250 %s" % self.fqdn)

    def smtp_EHLO(self, arg):
        if not arg:
            self.push("501 Syntax: EHLO hostname")
            return
        if self.seen_greeting:
            self.push("503 Duplicate HELO/EHLO")
        else:
            self.seen_greeting = arg
            self.extended_smtp = True
            if self.tls:
                self.push("250-%s on TLS" % self.fqdn)
            else:
                self.push("250-%s on plain" % self.fqdn)

            try:
                if self.server.ssl and not self.tls:
                    self.push("250-STARTTLS")
            except AttributeError:
                pass

            if self.data_size_limit:
                self.push("250-SIZE %s" % self.data_size_limit)
            self.push("250 HELP")

    def smtp_NOOP(self, arg):
        if arg:
            self.push("501 Syntax: NOOP")
        else:
            self.push("250 Ok")

    def smtp_QUIT(self, arg=""):
        # args is ignored
        self.push("221 Bye")
        self.close_when_done()

    def smtp_TIMEOUT(self, arg=""):
        self.push("421 2.0.0 Bye")
        self.close_when_done()

    # factored
    def getaddr(self, keyword, arg):
        address = None
        keylen = len(keyword)
        if arg[:keylen].upper() == keyword:
            address = arg[keylen:].strip()
            if not address:
                pass
            elif address[0] == "<" and address[-1] == ">" and address != "<>":
                # Addresses can be in the form <person@dom.com> but watch out
                # for null address, e.g. <>
                address = address[1:-1]
        return address

    def smtp_MAIL(self, arg):
        address = self.getaddr("FROM:", arg) if arg else None
        if not address:
            self.push("501 Syntax: MAIL FROM:<address>")
            return
        if self.mailfrom:
            self.push("503 Error: nested MAIL command")
            return
        self.mailfrom = address
        self.push("250 Ok")

    def smtp_RCPT(self, arg):
        if not self.mailfrom:
            self.push("503 Error: need MAIL command")
            return
        address = self.getaddr("TO:", arg) if arg else None
        if not address:
            self.push("501 Syntax: RCPT TO: <address>")
            return

        result = self.server.process_rcpt(address)
        if not result:
            self.rcpttos.append(address)
            self.push("250 Ok")
        else:
            self.push(result)

    def smtp_RSET(self, arg):
        if arg:
            self.push("501 Syntax: RSET")
            return
        # Resets the sender, recipients, and data, but not the greeting
        self.mailfrom = None
        self.rcpttos = []
        self.data = ""
        self.state = self.COMMAND
        self.push("250 Ok")

    def smtp_DATA(self, arg):
        if not self.rcpttos:
            self.push("503 Error: need RCPT command")
            return
        if arg:
            self.push("501 Syntax: DATA")
            return
        self.state = self.DATA
        self.terminator = "\r\n.\r\n"
        self.push("354 End data with <CR><LF>.<CR><LF>")

    def smtp_STARTTLS(self, arg):

        if arg:
            self.push("501 Syntax: STARTTLS")
            return
        self.push("220 Ready to start TLS")

        if self.data:
            self.push("500 Too late to changed")
            return

        try:
            self.conn = ssl.wrap_socket(self.conn, **self.server.ssl)
            self.state = self.COMMAND
            self.seen_greeting = 0
            self.rcpttos = []
            self.mailfrom = None
            self.tls = True
        except Exception as err:
            logger.error(err, exc_info=True)
            self.push("503 certificate is FAILED")
            self.close_when_done()

    def smtp_HELP(self, arg):

        if arg:
            if arg == "ME":
                self.push("504 Go to https://github.com/34nm/gsmtpd/issues for help")
            else:
                self.push("501 Syntax: HELP")
        else:
            self.push("214 SMTP server is running...go to website for further help")

    def handle_read(self):
        try:
            data = self.conn.recv(self.ac_in_buffer_size)
            if len(data) == 0:
                # issues 2 TCP connect closed will send a 0 size pack
                self.close_when_done()
        except socket.error:
            self.handle_error()
            return

        self.ac_in_buffer = self.ac_in_buffer + data.decode("utf-8")

        # Continue to search for self.terminator in self.ac_in_buffer,
        # while calling self.collect_incoming_data.  The while loop
        # is necessary because we might read several data+terminator
        # combos with a single recv(4096).

        while self.ac_in_buffer:
            lb = len(self.ac_in_buffer)
            logger.debug(self.ac_in_buffer)
            if not self.terminator:
                # no terminator, collect it all
                self.collect_incoming_data(self.ac_in_buffer)
                self.ac_in_buffer = ""
            elif isinstance(self.terminator, int):
                # numeric terminator
                n = self.terminator
                if lb < n:
                    self.collect_incoming_data(self.ac_in_buffer)
                    self.ac_in_buffer = ""
                    self.terminator = self.terminator - lb
                else:
                    self.collect_incoming_data(self.ac_in_buffer[:n])
                    self.ac_in_buffer = self.ac_in_buffer[n:]
                    self.terminator = 0
                    self.found_terminator()
            else:
                # 3 cases:
                # 1) end of buffer matches terminator exactly:
                #    collect data, transition
                # 2) end of buffer matches some prefix:
                #    collect data to the prefix
                # 3) end of buffer does not match any prefix:
                #    collect data
                terminator_len = len(self.terminator)
                index = self.ac_in_buffer.find(self.terminator)
                if index != -1:
                    # we found the terminator
                    if index > 0:
                        # don't bother reporting the empty string (source of subtle bugs)
                        self.collect_incoming_data(self.ac_in_buffer[:index])
                    self.ac_in_buffer = self.ac_in_buffer[index + terminator_len :]
                    # This does the Right Thing if the terminator is changed here.
                    self.found_terminator()
                else:
                    # check for a prefix of the terminator
                    index = find_prefix_at_end(self.ac_in_buffer, self.terminator)
                    if index:
                        if index != lb:
                            # we found a prefix, collect up to the prefix
                            self.collect_incoming_data(self.ac_in_buffer[:-index])
                            self.ac_in_buffer = self.ac_in_buffer[-index:]
                        break
                    else:
                        # no prefix, collect it all
                        self.collect_incoming_data(self.ac_in_buffer)
                        self.ac_in_buffer = ""

    def handle_error(self):
        self.close_when_done()

    def close_when_done(self):

        if not self.conn.closed:
            logger.debug("CLOSED %s" % self.conn)
            self.conn.close()
        self.closed = True
