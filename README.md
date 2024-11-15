# create-ssh-config

Create a SSH config file for multiple hosts and proxyjumps.
Configured with a JSON which defines each host and its hostnames.

```json
[
    {
        "host": "host1",
        "user": "user1",
        "auth": "password,publickey", # optional, default: publickey
        "identityfile": "/path/to/identityfile", # optional, default: ~/.ssh/id_ed25519
        "hostname": [
            # at least one hostname is required
            # the last hostnames check-subnet must be undefined or null
            # everything else is optional
            # if the check-subnet is "ping" the hostname is used.
            {
                # everything is optional
                "hostname": "host1.example.com", # no default
                "proxyjump": "other host" # default: none
                "check-subnet": "ping", # default: arguments to check_subnet script
                                        # if ping, the hostname is used
                "port": 1222 # default: 22
            }
            #
        ]
    }
]
```
