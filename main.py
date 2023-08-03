import ossapi
from ossapi import Ossapi
import discord
from discord.ext import commands
import mania_ur_estimator
import taiko_ur_estimator
import osu_ur_estimator

osu_api = Ossapi(00000, "input your key here")
discord_token = 'input your token here'

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='&', intents=intents)


def geosum(values: list):
    if len(values) == 0:
        return 0

    geosum = 0
    index = 0
    for n in values:
        geosum += n * 0.95**index
        index += 1

    return geosum


ur_estimators = {
    'mania' : mania_ur_estimator.unstable_rate,
    'taiko' : taiko_ur_estimator.unstable_rate,
    'osu'   : osu_ur_estimator.unstable_rate,
}


@bot.command()
async def calculate(ctx, url):
    if "osu.ppy.sh/scores/" not in url:
        pass

    url_groups = url.split("/")
    mode = url_groups[url_groups.index("scores") + 1]
    score_id = url_groups[url_groups.index("scores") + 2]

    if mode not in ur_estimators:
        pass

    score_stats = osu_api.score(mode, int(score_id)).statistics
    score_mods = osu_api.score(mode, int(score_id)).mods
    beatmap = osu_api.score(mode, int(score_id)).beatmap

    estimated_ur = ur_estimators[mode](score_stats, beatmap, score_mods)

    await ctx.send(f"Estimated {mode} unstable rate: {estimated_ur:.2f}")


@bot.command()
async def profile(ctx, mode, user_input: str):
    if mode not in ur_estimators:
        pass

    if "osu.ppy.sh/users/" in user_input:
        url_groups = user_input.split("/")
        user_arg = url_groups[url_groups.index("users") + 1]
    else:
        user_arg = user_input

    user = osu_api.user(user_arg)
    user_id = user.id
    user_name = user.username

    user_scores = osu_api.user_scores(user_id=user_id, mode=mode, type="best", limit=100)

    unstable_rate_list = []

    index = 0
    while index < len(user_scores):
        current_score = user_scores[index]

        estimated_ur = ur_estimators[mode](current_score.statistics, current_score.beatmap, current_score.mods)

        unstable_rate_list.append(estimated_ur)

        index += 1

    await ctx.send(f"Average unweighted UR of {user_name}'s {mode} scores: {sum(unstable_rate_list)/len(unstable_rate_list):.2f}\n"
                   f"Average weighted UR of {user_name}'s {mode} scores: {geosum(unstable_rate_list) / (20 * (1 - 0.95**100)):.2f}")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}.')


bot.run(discord_token)
