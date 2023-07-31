from ossapi import Ossapi
import discord
import mania_ur_estimator
import taiko_ur_estimator
import osu_ur_estimator

osu_api = Ossapi(00000, 'insert key here')
discord_token = 'insert token here'

intents = discord.Intents.none()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}.')


@client.event
async def on_message(message):
    if "osu.ppy.sh/scores/" in message.content:
        # Find the game mode of the score
        message_groups = message.content.split(" ")

        index = 0
        for string in message_groups:
            if "osu.ppy.sh/scores/" in string:
                break
            else:
                index += 1

        url = message_groups[index]
        url_groups = url.split("/")
        mode = url_groups[url_groups.index("scores") + 1]
        score_id = url_groups[url_groups.index("scores") + 2]

        if not mode == "osu" or mode == "mania" or mode == "taiko":
            pass

        score_statistics = osu_api.score(mode, score_id).statistics
        score_mods = str(osu_api.score(mode, score_id).mods)
        beatmap = osu_api.score(mode, score_id).beatmap

        if mode == "mania":
            estimated_ur = mania_ur_estimator.unstable_rate(score_statistics, beatmap, score_mods)
        elif mode == "taiko":
            estimated_ur = taiko_ur_estimator.unstable_rate(score_statistics, beatmap, score_mods)
        elif mode == "osu":
            estimated_ur = osu_ur_estimator.unstable_rate(score_statistics, beatmap, score_mods)

        await message.reply(f"Estimated {mode} unstable rate: {estimated_ur:.2f}")


client.run(discord_token)
