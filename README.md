# mottbot

Star Citizen mo.trader tracker bot for orgs in discord.

### To do:

  * proper devops (terraform, pytoml, python packaging etc)
  * refactor bot and response to use modern discord.py command extension tools
  * refactor to be as async as possible - remove requests library
  * Give advice when an image fails to be read (crop to just the MO.TRADER box before sending screenshot, make sure you are taking a screenshot rather than photographing your screen (the pixels of your monitor mess with my computer vision), check above for examples by other users)
  * provide option to follow up a failed image by entering the data by hand (e.g `!motrader correct` to cancel their previous transaction and change its value with the command only operating for that specific user in that channel.)
  * add column to database that reflects if verified by OCR or is a correction or from the `pay` command

