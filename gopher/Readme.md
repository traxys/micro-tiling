# Golfer
This is a very basic gopher server only serving text files. Default port is 3333


There is also commands with selector `!/<name>`.


### Commands ###
- `newfile`: tells the server a file was added
- `notify ADDRESS:PORT`: tells the server to notify that socket of any new file
- `delete SELECTOR`: ask the server to delete the file indicated by the `SELECTOR`
