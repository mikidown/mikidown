import datetime
from enum import Enum
import shlex
import subprocess

#BANNED_COMMANDS={'rm', 'cp', 'mv', 'unlink', 'mkdir', 'rmdir'}

class TitleType(Enum):
    FSTRING  = 0
    DATETIME = 1
    #COMMAND  = 2

def makeDefaultBody(title, dt_in_body_txt):
    return makeTemplateBody(TitleType.FSTRING, "{}", userinput=title, dt_in_body_txt=dt_in_body_txt)

def makeTemplateBody(title_type, title, dt_in_body=True,
        dt_in_body_fmt="%Y-%m-%d", dt_in_body_txt="Created {}", 
        userinput="", body=""):

    dtnow = datetime.datetime.now()
    if title_type == TitleType.FSTRING:
        filled_title = title.format(userinput)
    elif title_type == TitleType.DATETIME:
        filled_title = dtnow.strftime(title)

    #elif title_type == TitleType.COMMAND:
    #    args = shlex.split(title)
    #    if args[0] in BANNED_COMMANDS:
    #        raise ValueError("{} contains banned command {}".format(args[0]))
    #    filled_title = subprocess.check_output(args).decode('utf-8')

    else:
        return

    if dt_in_body is True:
        formatted_dt = dt_in_body_txt.format(dtnow.strftime(dt_in_body_fmt))
        return "# {}\n{}\n\n{}".format(filled_title, formatted_dt, body)
    else:
        return "# {}\n{}".format(filled_title, body)
