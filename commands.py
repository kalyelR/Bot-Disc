from discord.ext import commands
from views import DivisaoTimesView, BotaoMoverSelecionados
from config import CANAL_DESTINO_ID

def eh_admin_ou_cs_admin():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        for role in ctx.author.roles:
            if role.name.lower() == "Bot Commander":
                return True
        raise commands.MissingRole("Administrador ou CS ADMIN")
    return commands.check(predicate)

def setup_commands(bot):
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("❌ Você não tem o cargo necessário para usar esse comando.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar esse comando.")
        else:
            raise error

    @bot.command()
    @eh_admin_ou_cs_admin()
    async def dividir(ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Você precisa estar em um canal de voz para usar este comando.")
            return

        canal = ctx.author.voice.channel
        jogadores = [m for m in canal.members if not m.bot]

        if not jogadores:
            await ctx.send("❌ Nenhum jogador conectado neste canal de voz.")
            return

        view = DivisaoTimesView(jogadores, ctx.author.id)
        await ctx.send(
            content="👥 Escolha os jogadores para os times:",
            embed=view.gerar_embed(),
            view=view
        )

    @bot.command()
    @eh_admin_ou_cs_admin()
    async def mover_todos(ctx):
        view = BotaoMoverSelecionados()
        await ctx.send("Clique para mover os jogadores!!", view=view)