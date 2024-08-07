# infernal

A tool for getting answers to MyTestX tests distributed over a local network

The program downloads the test file and then automatically opens it in the editor, which allows you to see the answers

## Using

```shell
python main.py [options]
```

| Option          | Description                                                                                                      |
|-----------------|------------------------------------------------------------------------------------------------------------------|
| `-h` `--help`   | Help message                                                                                                     |
| `--ip`          | IP address or domain of the server PC (default: `127.0.0.1`)                                                     |
| `--port`        | Port of server PC (default: `5005`)                                                                              |
| `--folder`      | Name of folder for saving test files (default: `tests`)                                                          |
| `--user`        | The username on behalf of which the test will be received is displayed only in the server logs (default: `User`) |
| `-F` `--force`  | Faster script execution without outputting information logs                                                      |
| `-d` `--delete` | Delete test file after closing editor                                                                            |

> [!WARNING]
> `MTE.exe` must be located in the same directory with `infernal.py`
