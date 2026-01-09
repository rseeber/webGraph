import datetime

file = None

def setFile(f):
    global file
    file = f

# Print's msg, prepended with a timestamp. It also saves it to the log file.
def write(msg):
    # Create the output
    myTime = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")
    ouput = f"[{myTime}]: {msg}"
    # Print it
    print(ouput)
    # Log it
    with open(file, "a") as f:
        f.write(ouput+"\n")