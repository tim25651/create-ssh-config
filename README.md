# create-ssh-config

Create a SSH config file for multiple hosts and proxyjumps.
Configured with a YAML which defines each host and its hostnames.
A schema to validate against is also in the src/create-ssh-config directory.
```yaml
---
- host: host1
  user: user1
  auth: # optional, default: publickey
    - password
    - publickey
  identityfile: "/path/to/identityfile" # optional, default: ~/.ssh/id_ed25519
  hostnames:
    # at least one hostname is required
    # the last hostnames check-subnet must be undefined or null
    # everything else is optional
    # if the check-subnet is "ping" the hostname is used.
    - hostname: host1.example.com # no default
      proxyjump: other host # default: none
      check-subnet:
        ping # default: arguments to check_subnet script
        # if ping, the hostname is used
      port: 1222 # default: 22
      # but everything is optional
```
