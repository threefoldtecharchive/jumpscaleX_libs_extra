from Jumpscale import j

# import asyncio
from urllib.parse import urlparse

# import logging

# class AllHandler(logging.Handler):
#     def emit(self, record):
#         print(record)


# class WgetReturnProtocol(asyncio.SubprocessProtocol):
#     def __init__(self, exit_future):
#         self.exit_future = exit_future
#         self.output = bytearray()

#     def pipe_data_received(self, fd, data):
#         self.output.extend(data)
#         print(data)

#     def process_exited(self):
#         self.exit_future.set_result(True)


# h = AllHandler()
# logging.getLogger("asyncio").addHandler(h)

JSBASE = j.baseclasses.object


class Offliner(j.baseclasses.object):

    """
    functionality to inspect objectr structure and generate apifile
    """

    __jslocation__ = "j.tools.offliner"

    # @asyncio.coroutine
    def getSiteDownloadCmd(self, url, dest="", level=5, docElementsOnly=True, restrictToDomain=True):
        """
        download all docs from url to dest
        if dest=="" then use current dir and use url as subdir
        """
        cmd = ""
        if dest != "":
            cmd += "cd %s;" % dest
            j.sal.fs.createDir(dest)

        cmd += "wget --execute robots=off --recursive --no-clobber --page-requisites --html-extension --convert-links"
        cmd += " --restrict-file-names=windows --continue --user-agent=Mozilla"
        cmd += " --no-parent"
        cmd += " -l %s" % level
        if docElementsOnly:
            cmd += " --accept jpg,gif,png,jpeg,html,htm,css,js"
        if restrictToDomain:
            parsed = urlparse(url)
            domain = parsed.netloc
            cmd += " --domains %s" % domain

        cmd += " %s" % url
        self._log_debug(cmd)
        return cmd

        # # Create the subprocess, redirect the standard output into a pipe
        # create = asyncio.create_subprocess_shell(cmd,stdout=asyncio.subprocess.PIPE)

        # exit_future = asyncio.Future(loop=loop)

        # # Create the subprocess controlled by the protocol DateProtocol,
        # # redirect the standard output into a pipe
        # create = loop.subprocess_exec(lambda: DateProtocol(exit_future),
        #                               sys.executable, '-c', code,
        #                               stdin=None, stderr=None)
        # transport, protocol = yield from create

        # # Wait for the subprocess exit using the process_exited() method
        # # of the protocol
        # yield from exit_future

        # # Close the stdout pipe
        # transport.close()

        # # Read the output which was collected by the pipe_data_received()
        # # method of the protocol
        # data = bytes(protocol.output)
        # return data.decode('ascii').rstrip()

    def getPDFs(self, url, dest=""):
        "--accept=pdf"

    # def getSites(self,urls,dest="",level=5,docElementsOnly=True,restrictToDomain=True):
    #     # loop = asyncio.get_event_loop()
    #     # tasks=[]
    #     # for url in urls:
    #     #     tasks.append(asyncio.ensure_future(self._getSite(url,dest,level,docElementsOnly,restrictToDomain)))
    #     # loop.run_until_complete(asyncio.wait(tasks))
    #     # loop.close()

    #     for url in urls:


# examples from http://www.labnol.org/software/wget-command-examples/28750/
