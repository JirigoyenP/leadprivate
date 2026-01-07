from events4ebombo.bot4events import Bot4events
from datetime import datetime
bot=Bot4events()
#bot.modFuncaptcha()
#bot.passFunCaptcha()
#bot.changeToRecent()
bot.enterLinkedin()

#bot.specificSearch()
#bot.changeToRecent()
bot.linkedinPostsFoundViaSearching()
postsToFilter=bot.getHTMLPosts()
bot.linkedinPostsOnFeed(postsToFilter)
#bot.isEmpty()
bot.savePosts()
#bot.saveErrors()
#bot.postLinkedin(,datetime.now()#rawposts,time
#bot.verPostsGuardados()
#bot.verErrores()
