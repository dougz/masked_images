#!/usr/bin/python3

import argparse
import asyncio
import collections
import html
import itertools
import json
import os
import random
import time
import unicodedata

import http.client
import tornado.web

import scrum


def canonicalize_answer(text):
  text = unicodedata.normalize("NFD", text.upper())
  out = []
  for k in text:
    cat = unicodedata.category(k)
    # Letters only.
    if cat[:1] == "L":
      out.append(k)
  return "".join(out)


class Logo:
  def __init__(self, number, answer):
    self.number = number
    self.filename = f"{number:02d}.png"
    self.display = f"{number}. {answer}"
    self.answer = canonicalize_answer(answer)


class GameState:
  BY_TEAM = {}

  @classmethod
  def set_globals(cls, options, logos):
    cls.options = options
    cls.logos = logos

  @classmethod
  def get_for_team(cls, team):
    if team not in cls.BY_TEAM:
      cls.BY_TEAM[team] = cls(team)
    return cls.BY_TEAM[team]

  def __init__(self, team):
    self.team = team
    self.sessions = {}
    self.wid_sessions = {}
    self.running = False
    self.cond = asyncio.Condition()

    self.current_word = None
    self.solved = set()
    self.venn_centers = set()
    self.widq = collections.deque()
    self.wids = {}

    if self.options.min_players is not None:
      self.min_size = self.options.min_players
    else:
      self.min_size = max(2, (team.size + 1) // 4)
      if self.min_size > 20:
        self.min_size = 20

  async def on_wait(self, session, wid):
    now = time.time()
    wid = f"w{wid}"
    self.widq.append((wid, now))

    count = self.wids[wid] = self.wids.get(wid, 0) + 1
    if count == 1:
      # a new wid has been issued
      async with self.cond:
        self.cond.notify_all()

    self.wid_sessions[wid] = session

    async with self.cond:
      if session not in self.sessions:
        self.sessions[session] = None
        self.cond.notify_all()


  async def run_game(self):
    while True:
      count = len(self.sessions)
      if count >= self.min_size: break
      text = (
        f"You need {self.min_size} sports fans to start the game.<br>"
        f"{count} {'is' if count == 1 else 'are'} currently waiting.")
      msg = {"method": "show_message", "text": text}
      await self.team.send_messages([msg], sticky=1)
      async with self.cond:
        await self.cond.wait()

    for logo in itertools.cycle(self.logos):
      self.current_logo = logo

      if logo not in self.solved:
        d = {"method": "show_logo", "logo_url": self.options.assets[logo.filename]}
        await self.team.send_messages([d], sticky=1)

        deadline = time.time() + 5

        async with self.cond:
          while logo not in self.solved:
            timeout = deadline - time.time()
            if timeout <= 0: break
            try:
              await asyncio.wait_for(self.cond.wait(), timeout)
            except asyncio.TimeoutError:
              pass

      if logo in self.solved:
        d = {"method": "show_answer",
             "logo_url": self.options.assets[logo.filename],
             "answer": logo.display}
        await self.team.send_messages([d], sticky=1)
        await asyncio.sleep(1.5)

      if len(self.solved) == len(self.logos): break

    d = {"method": "show_all",
         "multi": [[self.options.assets[logo.filename], logo.display] for logo in self.logos]}
    await self.team.send_messages([d], sticky=1)


  async def send_chat(self, text):
    d = {"method": "add_chat", "text": text}
    await self.team.send_messages([d])

  async def try_answer(self, answer):
    async with self.cond:
      if (self.current_logo not in self.solved and
          answer == self.current_logo.answer):
        self.solved.add(self.current_logo)
        self.cond.notify_all()

  async def set_name(self, session, name):
    self.sessions[session] = name

    players = []
    for n in self.sessions.values():
      if n:
        players.append((n.lower(), n))
      else:
        players.append(("zzzzzzzz", "anonymous"))

    players.sort()
    players = ", ".join(p[1] for p in players)
    players = html.escape(players)

    await self.team.send_messages([{"method": "players", "players": players}])


class MaskedImagesApp(scrum.ScrumApp):
  async def on_wait(self, team, session, wid):
    gs = GameState.get_for_team(team)

    if not gs.running:
      gs.running = True
      self.add_callback(gs.run_game)

    await gs.on_wait(session, wid)


class SubmitHandler(tornado.web.RequestHandler):
  def prepare(self):
    self.args = json.loads(self.request.body)

  async def post(self):
    scrum_app = self.application.settings["scrum_app"]
    team, session = await scrum_app.check_cookie(self)
    gs = GameState.get_for_team(team)

    submission = self.args["answer"]
    answer = canonicalize_answer(submission)
    who = self.args["who"].strip()
    if not who: who = "anonymous"
    print(f"{team}: {who} submitted {answer}")

    await gs.send_chat(f"<b>{who}</b> guessed \"{html.escape(submission)}\"")
    await gs.try_answer(answer)

    self.set_status(http.client.NO_CONTENT.value)


class NameHandler(tornado.web.RequestHandler):
  def prepare(self):
    self.args = json.loads(self.request.body)

  async def post(self):
    scrum_app = self.application.settings["scrum_app"]
    team, session = await scrum_app.check_cookie(self)
    gs = GameState.get_for_team(team)

    await gs.set_name(session, self.args.get("who"))
    self.set_status(http.client.NO_CONTENT.value)


class DebugHandler(tornado.web.RequestHandler):
  def get(self, fn):
    if fn.endswith(".css"):
      self.set_header("Content-Type", "text/css")
    elif fn.endswith(".js"):
      self.set_header("Content-Type", "application/javascript")
    with open(fn) as f:
      self.write(f.read())


def make_app(options):
  logos = [Logo(i+1, n) for (i, n) in enumerate(
    ("STEELERS",
     "BRUINS",
     "SABRES",
     "BLUE JAYS",
     "JETS",
     "PACERS",
     "NUGGETS",
     "RAPTORS",
     "FLAMES",
     "ISLANDERS",
     "WARRIORS",
     "TIMBERWOLVES",
     "OILERS",
     "TWINS",
     "CUBS",
     "MARINERS",
     "ASTROS",
     "RANGERS",
     "HAWKS",
     "NATIONALS",
     "PISTONS",
     "METS"))]

  assert len(logos) == 22

  GameState.set_globals(options, logos)

  handlers = [
    (r"/masksubmit", SubmitHandler),
    (r"/maskname", NameHandler),
  ]
  if options.debug:
    handlers.append((r"/maskdebug/(\S+)", DebugHandler))
  return handlers


def main():
  parser = argparse.ArgumentParser(description="Run the masked_images puzzle.")
  parser.add_argument("--debug", action="store_true",
                      help="Run in debug mode.")
  parser.add_argument("--assets_json", default=None,
                      help="JSON file for image assets")
  parser.add_argument("-c", "--cookie_secret",
                      default="snellen2020",
                      help="Secret used to create session cookies.")
  parser.add_argument("--listen_port", type=int, default=2005,
                      help="Port requests from frontend.")
  parser.add_argument("--wait_url", default="maskwait",
                      help="Path for wait requests from frontend.")
  parser.add_argument("--main_server_port", type=int, default=2020,
                      help="Port to use for requests to main server.")
  parser.add_argument("--min_players", type=int, default=None,
                      help="Number of players needed to start game.")

  options = parser.parse_args()

  assert options.assets_json
  with open(options.assets_json) as f:
    options.assets = json.load(f)

  app = MaskedImagesApp(options, make_app(options))
  app.start()


if __name__ == "__main__":
  main()

