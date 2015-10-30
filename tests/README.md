Commands used to copy the /sys/class node:

```sh
node=lego-sensor/sensor0
mkdir -p ./${node}
# Copy contents of special files, do not follow symlinks:
cp -P --copy-contents -r /sys/class/${node}/* ./${node}/
```
