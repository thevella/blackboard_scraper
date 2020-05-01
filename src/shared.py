debug = False
#blackBoardBaseURL = "lms.curtin.edu.au"
blackBoardBaseURL = 'uoit.blackboard.com'

valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-&'

#sanitizes the filenames for windows (and hopefully other OS' too!)
def sanitize(filename):
    filename = filename.strip()
    filename = filename.replace(":", "--").replace("/", "-")

    filename = ''.join(c for c in filename if c in valid_chars)
    try:
        while ((filename[len(filename)-1] == ' ') or (filename[len(filename)-1] == '.')):
            filename = filename[:-1]
        while (filename.count("  ") != 0):
            filename = filename.replace("  ", " ")
    except IndexError:
        if len(filename) < 1:
            return 'file_' + filename
        else:
            return filename.strip()
    return filename.strip()
