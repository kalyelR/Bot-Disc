import discord
from discord.ext import commands
import random
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

CANAL_TIME_1_ID = 1195347901153550357
CANAL_TIME_2_ID = 1398450603834740788
CANAIS_ORIGEM_IDS = [CANAL_TIME_1_ID, CANAL_TIME_2_ID]
CANAL_DESTINO_ID = 1399108412884779260

# ✅ Permite uso por administradores OU por quem tem o cargo "Bot Commander"
def eh_admin_ou_cs_admin():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        for role in ctx.author.roles:
            if role.name.lower() == "Bot Commander":
                return True
        raise commands.MissingRole("Administrador ou Bot Commander")
    return commands.check(predicate)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Você não tem o cargo necessário para usar esse comando.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar esse comando.")
    else:
        raise error


class DivisaoTimesView(discord.ui.View):
    def __init__(self, membros, autor_id):
        super().__init__(timeout=300)
        self.membros = membros
        self.autor_id = autor_id
        self.selecionados_time_1 = set()
        self.selecionados_time_2 = set()
        self.atualizar_view()

    def atualizar_view(self):
        self.clear_items()
        self.add_item(SelectTime1(self.membros, self.selecionados_time_2))
        self.add_item(SelectTime2(self.membros, self.selecionados_time_1))
        self.add_item(BotaoEmbaralhar(self))
        self.add_item(BotaoConfirmarTimes(self))

    def gerar_embed(self):
        embed = discord.Embed(title="🏆 Times definidos!", color=discord.Color.green())
        embed.add_field(
            name=f"🔴 Time 1 (Total: {len(self.selecionados_time_1)})",
            value="\n".join(m.mention for m in self.selecionados_time_1) or "—",
            inline=True
        )
        embed.add_field(
            name=f"🔵 Time 2 (Total: {len(self.selecionados_time_2)})",
            value="\n".join(m.mention for m in self.selecionados_time_2) or "—",
            inline=True
        )
        return embed

class SelectTime1(discord.ui.Select):
    def __init__(self, membros, selecionados_time_2):
        self.membros_dict = {str(m.id): m for m in membros}
        options = [
            discord.SelectOption(label=m.display_name, value=str(m.id))
            for m in membros if m not in selecionados_time_2
        ]
        super().__init__(
            placeholder="🔴 Selecione jogadores para o Time 1",
            min_values=0,
            max_values=min(len(options), 25),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view: DivisaoTimesView = self.view
        if interaction.user.id != view.autor_id:
            await interaction.response.send_message("Você não pode editar os times.", ephemeral=True)
            return

        selecionados_ids = set(self.values)
        view.selecionados_time_1 = {self.membros_dict[i] for i in selecionados_ids}
        view.selecionados_time_2 = {m for m in view.selecionados_time_2 if m.id not in [int(i) for i in selecionados_ids]}
        view.atualizar_view()
        await interaction.response.edit_message(embed=view.gerar_embed(), view=view)

class SelectTime2(discord.ui.Select):
    def __init__(self, membros, selecionados_time_1):
        self.membros_dict = {str(m.id): m for m in membros}
        options = [
            discord.SelectOption(label=m.display_name, value=str(m.id))
            for m in membros if m not in selecionados_time_1
        ]
        super().__init__(
            placeholder="🔵 Selecione jogadores para o Time 2",
            min_values=0,
            max_values=min(len(options), 25),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view: DivisaoTimesView = self.view
        if interaction.user.id != view.autor_id:
            await interaction.response.send_message("Você não pode editar os times.", ephemeral=True)
            return

        selecionados_ids = set(self.values)
        view.selecionados_time_2 = {self.membros_dict[i] for i in selecionados_ids}
        view.selecionados_time_1 = {m for m in view.selecionados_time_1 if m.id not in [int(i) for i in selecionados_ids]}
        view.atualizar_view()
        await interaction.response.edit_message(embed=view.gerar_embed(), view=view)

class BotaoEmbaralhar(discord.ui.Button):
    def __init__(self, view_ref):
        super().__init__(label="🔀 Embaralhar times", style=discord.ButtonStyle.primary, row=2)
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_ref.autor_id:
            await interaction.response.send_message("Apenas quem iniciou pode embaralhar.", ephemeral=True)
            return

        jogadores = list(self.view_ref.membros)
        random.shuffle(jogadores)
        metade = len(jogadores) // 2
        self.view_ref.selecionados_time_1 = set(jogadores[:metade])
        self.view_ref.selecionados_time_2 = set(jogadores[metade:])
        self.view_ref.atualizar_view()
        await interaction.response.edit_message(embed=self.view_ref.gerar_embed(), view=self.view_ref)

class BotaoConfirmarTimes(discord.ui.Button):
    def __init__(self, view_ref):
        super().__init__(label="✅ Confirmar times e iniciar", style=discord.ButtonStyle.success, row=2)
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_ref.autor_id:
            await interaction.response.send_message("Apenas quem iniciou pode confirmar os times.", ephemeral=True)
            return

        guild = interaction.guild
        canal_1 = guild.get_channel(CANAL_TIME_1_ID)
        canal_2 = guild.get_channel(CANAL_TIME_2_ID)

        moved_1, moved_2 = [], []
        for membro in self.view_ref.selecionados_time_1:
            if membro.voice:
                try:
                    await membro.move_to(canal_1)
                    moved_1.append(membro.display_name)
                except:
                    pass
        for membro in self.view_ref.selecionados_time_2:
            if membro.voice:
                try:
                    await membro.move_to(canal_2)
                    moved_2.append(membro.display_name)
                except:
                    pass

        self.view_ref.clear_items()
        await interaction.response.defer()
       

class BotaoMoverSelecionados(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Mover usuários", style=discord.ButtonStyle.green)
    async def mover_todos(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_destino = interaction.guild.get_channel(CANAL_DESTINO_ID)

        if not isinstance(canal_destino, discord.VoiceChannel):
            await interaction.response.send_message("Canal de destino inválido.", ephemeral=True)
            return

        moved_count = 0
        for member in interaction.guild.members:
            if (member.voice and member.voice.channel and member.voice.channel.id in CANAIS_ORIGEM_IDS
                    and member.voice.channel != canal_destino and not member.bot):
                try:
                    await member.move_to(canal_destino)
                    moved_count += 1
                except discord.Forbidden:
                    continue
                except Exception:
                    continue

        await interaction.response.send_message(f"{moved_count} usuário(s) movido(s) para {canal_destino.name}.")

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
    await ctx.send("Como ousas não obedecer a realeza??", view=view)
