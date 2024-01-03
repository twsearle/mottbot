# mottbot

Star Citizen mo.trader tracker bot for orgs in discord.

### To do:

  * Add back in print last transaction command
  * add error handlers to respond to bad argument formatting
  * add permissions check using discord checks
  * add column to database that reflects if verified by OCR or is a correction or from the `pay` command
  * Give advice when an image fails to be read (crop to just the MO.TRADER box before sending screenshot, make sure you are taking a screenshot rather than photographing your screen (the pixels of your monitor mess with my computer vision), check above for examples by other users)
  * look into converters to see if I still want them
  * test that everything is asynced as we want
  * provide option to follow up a failed image by entering the data by hand (e.g `!motrader correct` to cancel their previous transaction and change its value with the command only operating for that specific user in that channel.)
  * proper devops (terraform, pytoml, python packaging etc)

