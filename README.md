# mottbot

Star Citizen mo.trader tracker bot for orgs in discord.

### To do:

  * decide how to handle `create` vs account creation based on the bot being added to channel? Use reactions of x?
  * add permissions check using discord checks
  * Give advice when an image fails to be read (crop to just the MO.TRADER box before sending screenshot, make sure you are taking a screenshot rather than photographing your screen (the pixels of your monitor mess with my computer vision), check above for examples by other users)
  * look into converters to see if I still want them
  * test that everything is asynced as we want
  * provide option to follow up a failed image by entering the data by hand (e.g `!motrader correct` to cancel their previous transaction and change its value with the command only operating for that specific user in that channel.)
  * proper devops (terraform, pytoml, python packaging etc)

