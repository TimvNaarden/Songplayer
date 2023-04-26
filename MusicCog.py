import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import pprint


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.connection = None
        self.bot = bot

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.vc = None

    def search_yt(self, item):
        item += " music video lyrics"
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False
        return {'source': info['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            self.music_queue.pop(0)

            self.connection.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        print(self.music_queue)
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']

            if self.vc is None:
                print(self.music_queue[0][1])
                self.vc = ctx.author.voice.channel

                try:
                    self.connection = await self.vc.connect()
                except Exception as a:
                    print(a)

            else:
                await self.connection.move_to(ctx.author.voice.channel)

            self.music_queue.pop(0)
            try:
                self.connection.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
            except Exception as e:
                print(e)
        else:
            self.is_playing = False

    def clear(self):
        self.connection = None
        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.vc = None

    @commands.command(name="play", aliases=["p", "playing"], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)

        try:
            print("User in in voice channel " + str(ctx.author.voice.channel))
        except Exception as e:
            print("User is not in a voice channel, error:" + str(e))
            await ctx.send("You are not in a voice channel")
            return

        if self.is_paused:
            await ctx.send("Queue is currently paused, resuming the queue.")
            self.vc.resume()

        song = self.search_yt(query)
        if not song:
            await ctx.send(
                "Could not download the song. Incorrect format try another keyword. This could be due to playlist "
                "or a livestream format.")
        else:
            await ctx.send(f"{song['title']} added to the queue")
            self.music_queue.append([song, ctx.author.voice.channel])
            if not self.is_playing:
                await self.play_music(ctx)

    @commands.command(name="pause", help="pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.connection.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.connection.resume()

    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.connection.resume()

    @commands.command(name="skip", aliases=["s"], help="Skips the current playing song")
    async def skip(self, ctx, *args):
        if self.vc is not None and self.vc:
            self.connection.stop()
            self.is_playing = False
            self.is_paused = False
        if len(self.music_queue) > 0:
            await self.play_music(ctx)
        else:
            await self.connection.disconnect()

    @commands.command(name="queue", aliases=["q"], help="Displas all the songs in the current queue")
    async def queue(self, ctx):
        retval = ""

        for i in range(0, len(self.music_queue)):
            if i > 4: break
            retval += self.music_queue[i][0]['title'] + '\n'
        if retval != "":
            await ctx.send(retval)

        else:
            await ctx.send("No music in the queue.")

    @commands.command(name="clear", aliases=["c", "bin"], help="stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        if self.vc is not None and self.is_playing:
            await self.connection.disconnect()
        self.music_queue = []
        self.is_playing = False
        self.is_paused = False
        self.vc = None
        await ctx.send("Music queue cleared")

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot form the current channel")
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.connection.disconnect()

    @commands.command(name="get", help="Print the current variables in the console -> Debugging")
    async def get(self, ctx):
        pprint.pprint(vars(self))


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
