# Features

## Backup the published captions of all the videos of a YouTube channel

```
bin/backup.sh --channel CHANNEL_ID
```


## Backup the published captions of some videos

```
bin/backup.sh --videos VIDEO_ID_1 VIDEO_ID_2 ...
```


## Create issue⋅s for recent video⋅s of channel

```
bin/create-issues.sh --channel CHANNEL_ID
```


## Create issue⋅s for provided video⋅s

```
bin/create-issues.sh --videos VIDEO_ID_1 VIDEO_ID_2 ...
```


## It's also a webhook for github

Available at https://bot.insoumis.online

It's a simple flask app.


# Install

See [`bin/setup.sh`](bin/setup.sh).


# License

[Apache License v2.0](LICENSE)
