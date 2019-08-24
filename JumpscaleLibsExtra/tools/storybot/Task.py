from .utils import _find_second, _check_broken_links

from Jumpscale import j


class Task:
    """Represents a task
    """

    LIST_TITLE = "Tasks"

    def __init__(self, url="", description="", state="open", body="", update_func=None):
        """Task constructor
        
        Keyword Arguments:
            url str -- URL to task page (default: "")
            description str -- Task description (default: "")
            state str -- state of the story ("open", "closed") (default: "open")

        
        Raises:
            ValueError -- Empty description  
            ValueError -- Empty url
        """

        if description == "":
            raise j.exceptions.Value("description was not provided and is mandatory")
        if url == "":
            raise j.exceptions.Value("url was not provided and is mandatory")

        self.url = url
        self.description = description
        self.state = state
        self.body = body
        self._update_func = update_func

    def __repr__(self):
        return self.description

    def __eq__(self, other):
        return self.url == other

    @property
    def done_char(self):
        """Returns done character
        
        Returns:
            str -- char that defines the item done or not for markdown files
        """
        return "x" if self.state == "closed" else " "

    @property
    def md_item(self):
        """Returns the representation of the Task as a markdown list item
        
        Returns:
            str -- Task as mardown list item
        """
        return "- [%s] [%s](%s)" % (self.done_char, self.description, self.url)

    def index_in_body(self, body, start_i=0, end_i=-1):
        """Returns index of item in body
        Starting and ending from provided indexes

        Returns -1 if nor found
        
        Arguments:
            body str -- issue body to look up the index of the task
        
        Keyword Arguments:
            start_i int -- Start index if lookup (default: 0)
            end_i int -- End index of lookup (default: -1)
        
        Returns:
            int -- line index of item in body
        """

        lines = body.splitlines()[start_i : end_i + 1 if end_i != -1 else None]
        for i, line in enumerate(lines, start=start_i):
            if i > end_i and not end_i < 0:
                break
            # check if list item
            if not line.startswith("- ["):
                continue
            if _desc_in_line(line) == self.description:
                return i

        return -1

    def update_body(self, body):
        """Update the body of a task
        
        Arguments:
            body str -- Updated body for the task's issue
        """
        self._update_func(body)

    def check_broken_urls(self):
        """Iterates over story list, marks broken links (or unmark fixed links)
        Update body of issue if needed.
        """
        try:
            new_body = _check_broken_links(self.body, self.LIST_TITLE, self.url)
        except RuntimeError as err:
            self._log_error("Something went wrong checking for broken urls: %s" % err)
            return self.body

        if self.body != new_body:
            self._update_func(new_body)
            self._body = new_body


def _desc_in_line(line):
    """Returns task description from provided list line
    String is empty when description was not found
    
    Arguments:
        line str -- Line of a task list
    
    Returns:
        string -- description
    """
    start_i = _find_second(line, "[")
    end_i = _find_second(line, "]")

    if start_i != -1 and end_i != -1:
        return line[start_i : end_i - 1].strip()

    return ""
