from .base import KhlReader


class GameBroadcastReader(KhlReader):

    def __init__(self, tournament_id, game_id, khl_domain='www.khl.ru'):
        super().__init__()
        # reader vars
        self.api_payload = f'values[tournament]={tournament_id}&values[gameid]={game_id}'
        self.source_page_url = f'https://{khl_domain}/game/{tournament_id}/{game_id}/text/'
        self.text_api_url = f'https://{khl_domain}/rest/game/text/'
        self.header_api_url = f'https://{khl_domain}/rest/game/header/'
        self.tournament_id = tournament_id
        self.game_id = game_id
        self._goals_extracted = False
        self._penalties_extracted = False
        # source data
        self.game_data = None
        self.header_data = None
        self.vr_reasons = {}
        self.vr_initiators = {}
        self.text_events = {}
        self.playbyplay_events = {}
        # mapped source data
        self.players_by_id = {}
        self.referees_by_id = {}
        self.players_by_jn = {}
        # output data
        self._info = {}
        self.home_team = None
        self.home_lineup = {}
        self.home_coach = {}
        self.home_player_stats = {}
        self.home_team_stats = {}
        self.visitor_team = None
        self.visitor_lineup = {}
        self.visitor_coach = {}
        self.visitor_player_stats = {}
        self.visitor_team_stats = {}
        self._goals = []
        self._disallowed_goals = []
        self._video_reviews = []
        self._penalties = []
        self._penalty_shots = []
        self._shootouts = []
        self._goalie_subs = []

    async def _run_ops(self):
        self.api_payload += f'&sessid={self.khl_sessid}'
        await self._asyncio_gather(
            self._fetch_api_data(self.text_api_url, 'game_data'),
            self._fetch_api_data(self.header_api_url, 'header_data')
        )
        self._extract_api_data()

    def _extract_api_data(self):
        if self.game_data:
            self.vr_reasons = self.game_data.get('TEXT', {}).get('vr_reason', {})
            self.vr_initiators = self.game_data.get('TEXT', {}).get('vr_ini', {})
            self.game_data = self.game_data.get('game', {})
            self._extract_teams()
            self._extract_text_events()
            # self._extract_playbyplay_events()
            self._extract_referees()
            self._extract_players()

    def _extract_text_events(self):
        for period_data in reversed(self.game_data.get('tab_events', [])):
            period = period_data.get('period')
            for event in reversed(period_data.get('events', ())):
                event_type = event.get('type', 'unknown')
                if event_type not in self.text_events:
                    self.text_events[event_type] = []
                self.text_events[event_type].append({**event, 'period': period})

    def _extract_playbyplay_events(self):
        game_legend = self.game_data.get('tab_playbyplay', {}).get('gameLegend', {})
        for period, period_data in game_legend.items():
            if isinstance(period_data, list):
                for event in reversed(period_data):
                    event_type = event.get('type', 'unknown')
                    if event_type not in self.playbyplay_events:
                        self.playbyplay_events[event_type] = []
                    self.playbyplay_events[event_type].append({**event, 'period': period})

    def _extract_teams(self):
        teams = self.game_data.get('teams', {})
        self.home_team, self.visitor_team = teams.get('home', {}), teams.get('visitor', {})
        if self.header_data:
            extra_info = self.header_data.get('game', {})
            self.home_team.update({
                'khl_id': extra_info.get('teama'),
                'name_en': extra_info.get('homeName_en'),
                'short_name': extra_info.get('homeName_l3'),
                'short_name_en': extra_info.get('homeName_l3_en'),
            })
            self.visitor_team.update({
                'khl_id': extra_info.get('teamb'),
                'name_en': extra_info.get('visitorName_en'),
                'short_name': extra_info.get('visitorName_l3'),
                'short_name_en': extra_info.get('visitorName_l3_en'),
            })

    def _extract_players(self):
        players = self.game_data.get('players', {})
        game_item = self.game_data.get('gameItem', {})
        players_a = [{**p, 'id': int(p['id'])} for p in players.get('A', {}).values()]
        players_b = [{**p, 'id': int(p['id'])} for p in players.get('B', {}).values()]
        self.players_by_jn = {'A': {p['jn']: p for p in players_a}, 'B': {p['jn']: p for p in players_b}}
        self.players_by_id = {p['id']: p for p in players_a + players_b}
        self.home_gk_jn = game_item.get('gkA')
        self.visitor_gk_jn = game_item.get('gkB')

    def _extract_referees(self):
        game_item = self.game_data.get('gameItem', {})
        referees = (
            {
                'id': game_item.get('idmainref1'), 'name': game_item.get('refm1'),
                'number': game_item.get('jnmainref1'), 'position': 'referee'
            },
            {
                'id': game_item.get('idmainref2'), 'name': game_item.get('refm2'),
                'number': game_item.get('jnmainref2'), 'position': 'referee'
            },
            {
                'id': game_item.get('idlineref1'), 'name': game_item.get('refl1'),
                'number': game_item.get('jnlineref1'), 'position': 'linesman'
            },
            {
                'id': game_item.get('idlineref2'), 'name': game_item.get('refl2'),
                'number': game_item.get('jnlineref2'), 'position': 'linesman'
            }
        )
        self.referees_by_id = {ref['id']: ref for ref in referees}

    @property
    def info(self):
        if not self._info and self.header_data:
            info = self.header_data.get('game', {})
            online = self.header_data.get('online', {})
            self._info = {
                'attendance': info.get('attendance'),
                'arena_id': info.get('arenaid'),
                'arena': info.get('arena'),
                'arena_en': info.get('arena_en'),
                'city': info.get('arena_city'),
                'city_en': info.get('arena_city_en'),
                'home_score': online.get('homeScore', info.get('homeScore')),
                'visitor_score': online.get('visitorScore', info.get('visitorScore')),
                'ots': info.get('ots'),
                'is_over': info.get('approved', 0) == 1
            }
        return self._info

    @property
    def team_info(self):
        return self.home_team, self.visitor_team

    @property
    def lineup(self):
        if not (self.home_lineup or self.visitor_lineup) and self.game_data:
            lineups = {'A': {}, 'B': {}}
            start_gk = {'A': self.home_gk_jn, 'B': self.visitor_gk_jn}
            for player in self.players_by_id.values():
                line = int(player['line']) if player['pos'] != 'в' else 0
                if line not in lineups[player['teamAB']]:
                    lineups[player['teamAB']][line] = []
                lineups[player['teamAB']][line].append({
                    **self._get_short_profile(player),
                    'in_start': line == 1 or line == 0 and player['jn'] == start_gk[player['teamAB']],
                })
            self.home_lineup = dict(sorted(lineups['A'].items()))
            self.visitor_lineup = dict(sorted(lineups['B'].items()))
        return self.home_lineup, self.visitor_lineup

    @property
    def referees(self):
        return list(self.referees_by_id.values())

    @property
    def coaches(self):
        if not (self.home_coach or self.visitor_coach) and self.header_data:
            for team_ab, coach in self.header_data.get('proto', {}).get('coaches', {}).items():
                if isinstance(coach, dict):
                    coach['id'] = self._int(coach.pop('link').strip('/').split('/')[-1])
                    setattr(self, 'home_coach' if team_ab == 'A' else 'visitor_coach', coach)
        return self.home_coach, self.visitor_coach

    @property
    def player_stats(self):
        if not (self.home_player_stats or self.visitor_player_stats) and self.game_data:
            stats_map = {'A': self.home_player_stats, 'B': self.visitor_player_stats}
            stats = self.game_data.get('tab_stats', {}).get('playerstats', {})
            for t in ('A', 'B'):
                for period_idx, period_stats in enumerate(stats.get(t, [])):
                    period_name = self._get_period_shortname(period_idx)
                    period_data = period_stats.get('data', {})
                    stats_map[t][period_name] = []
                    for item in period_data:
                        player = self.players_by_jn[t].get(item['jn'], {})
                        stats_map[t][period_name].append({
                            'khl_id': player.get('id'),
                            'full_name': player.get('name'),
                            'number': player.get('jn'),
                            'captain': self.CAPTAIN_MAP.get(player.get('ca')),
                            **self._transform_player_stats(item.get('stats', {}))
                        })
        return self.home_player_stats, self.visitor_player_stats

    @property
    def team_stats(self):
        if not (self.home_team_stats or self.visitor_team_stats) and self.game_data:
            stats = self.game_data.get('tab_stats', {}).get('teamstats', {})
            for period_idx, period_stats in enumerate(stats):
                period_name = self._get_period_shortname(period_idx)
                home_data, visitor_data = period_stats.get('data', [{}, {}])
                self.home_team_stats[period_name] = home_data.get('stats')
                self.visitor_team_stats[period_name] = visitor_data.get('stats')
            self._aggregate_team_stats()
        return self.home_team_stats, self.visitor_team_stats

    @property
    def goals(self):
        self._extract_goals_and_reviews()
        return self._goals

    @property
    def disallowed_goals(self):
        self._extract_goals_and_reviews()
        return self._disallowed_goals

    @property
    def video_reviews(self):
        self._extract_goals_and_reviews()
        return self._video_reviews

    @property
    def penalties(self):
        self._extract_penalties()
        return self._penalties

    @property
    def penalty_shots(self):
        self._extract_penalties()
        return self._penalty_shots

    @property
    def shootouts(self):
        if not self._shootouts:
            result_map = {'0': 'goal', '1': 'save', '2': 'miss'}
            for event in self.text_events.get('bu', []):
                self._shootouts.append({
                    'event_num': len(self._shootouts) + 1,
                    'team_side': event['team'],
                    'team_id': (self.home_team if event['team'] == 'A' else self.visitor_team).get('cid'),
                    'player_id': self.players_by_jn[event['team']].get(int(event['scorer']), {}).get('id'),
                    'player_number': int(event['scorer']),
                    'goalie_id': self.players_by_jn[event['oppoAB']].get(int(event['goalkeeper']), {}).get('id'),
                    'goalie_number': int(event['goalkeeper']),
                    'home_so_score': event['scA'],
                    'visitor_so_score': event['scB'],
                    'result': result_map[event['result']]
                })
        return self._shootouts

    @property
    def goalie_subs(self):
        if not self._goalie_subs:
            for event in self.text_events.get('gc', []):
                gk_out = self.players_by_jn[event['teamAB']].get(int(event['prevGk']), {})
                gk_in = self.players_by_jn[event['teamAB']].get(int(event['gkJn']), {})
                self._goalie_subs.append({
                    'event_num': len(self._goalie_subs) + 1,
                    'ingame_time': event['time'],
                    'ingame_time_int': event['time_sec'],
                    'period': self._get_period_shortname(event['period']),
                    'team_side': event['teamAB'],
                    'team_id': self.home_team.get('cid') if event['teamAB'] == 'A' else self.visitor_team.get('cid'),
                    'goalie_out_id': gk_out.get('id'),
                    'goalie_out_number': gk_out.get('jn'),
                    'goalie_in_id': gk_in.get('id'),
                    'goalie_in_number': gk_in.get('jn'),
                })
        return self._goalie_subs

    def _extract_goals_and_reviews(self):
        if not self._goals_extracted:
            video_events = []
            for event_num, event in enumerate(self.text_events.get('go', [])):
                so_goal = event['time_sec'] == 3900 and event['rbm'] == '3'
                goal = {
                    'event_num': event_num + 1,
                    'ingame_time': event['time'],
                    'ingame_time_int': event['time_sec'],
                    'period': 'so' if so_goal else self._get_period_shortname(event['period']),
                    'team_side': event['team'],
                    'team_id': event['teamID'],
                    'pmg': -1 if event['rbm'] == '2' else self._int(event['rbm']),
                    'home_score': event['scA'],
                    'visitor_score': event['scB'],
                }
                for k in ['scorer', 'assist1', 'assist2']:
                    goal[f'{k}_number'] = self._int(event.get(k), None)
                    goal[f'{k}_id'] = self.players_by_jn[event['team']].get(goal[f'{k}_number'], {}).get('id')
                self._goals.append(goal)
                video_events.append({'k': f'g_{event_num}', 't': goal['ingame_time']})

            for event_num, event in enumerate(self.text_events.get('vr', [])):
                vr = {
                    'event_num': event_num + 1,
                    'ingame_time': event['time'],
                    'ingame_time_int': event['time_sec'],
                    'period': self._get_period_shortname(event['period']),
                    'initiator': self.vr_initiators.get(event['ini']),
                    'reason': self.vr_reasons.get(event['reason']),
                    'game_result': event['resGame'],
                    'vr_result': event['res'],
                    'referee': self.referees_by_id.get(int(event['referee']), {}),
                    'team_goal': event.get('teamGoal'),
                    'team_ab': event.get('teamAB')
                }
                self._video_reviews.append(vr)
                if vr['team_goal'] in ['goalA', 'goalB'] and vr['game_result'] != vr['vr_result']:
                    idx = len(self._disallowed_goals)
                    disallowed_goal = {
                        'event_num': idx + 1,
                        'ingame_time': vr['ingame_time'],
                        'ingame_time_int': vr['ingame_time_int'],
                        'period': vr['period'],
                        'team_side': vr['team_goal'][4],
                        'team_id': (self.home_team if vr['team_goal'][4] == 'A' else self.visitor_team).get('cid'),
                        'reason': vr['reason'],
                        'referee_name': vr['referee'].get('name'),
                        'referee_number': vr['referee'].get('number'),
                    }
                    video_events.append({'k': f'd_{idx}', 't': disallowed_goal['ingame_time']})
                    self._disallowed_goals.append(disallowed_goal)
            for idx, e in enumerate(sorted(video_events, key=lambda d: d['t'])):
                key = e['k'].split('_')
                if key[0] == 'g':
                    self._goals[int(key[1])]['video_event_num'] = idx + 1
                elif key[0] == 'd':
                    self._disallowed_goals[int(key[1])]['video_event_num'] = idx + 1
        self._goals_extracted = True

    def _extract_penalties(self):
        if not self._penalties_extracted:
            for event in self.text_events.get('pn', []):
                team_penalty = event['jn'] == '0'
                penalty_shot = event['pim'] == '0'
                player_number = int(event['served_jn'] if team_penalty else event['jn'])
                penalty = {
                    'ingame_time': event['time'],
                    'ingame_time_int': event['time_sec'],
                    'period': self._get_period_shortname(event['period']),
                    'team_side': event['team'],
                    'team_id': (self.home_team if event['team'] == 'A' else self.visitor_team).get('cid'),
                    'player_id': int(self.players_by_jn[event['team']].get(player_number, {}).get('id')),
                    'player_number': player_number,
                    'code': int(event['code']),
                    'reason': event['codeName'],
                }
                if penalty_shot:
                    self._penalty_shots.append({
                        'event_num': len(self._penalty_shots) + 1,
                        'shot_by_id': int(self.players_by_jn[event['oppoAB']].get(int(event['b_jn']), {}).get('id')),
                        'shot_by_number': int(event['b_jn']),
                        **penalty
                    })
                else:
                    self._penalties.append({
                        'event_num': len(self._penalties) + 1,
                        'pim': int(event['pim']),
                        'team_penalty': team_penalty,
                        **penalty
                    })
        self._penalties_extracted = True

    def _get_short_profile(self, player: dict) -> dict:
        return {
            'player_id': player['id'],
            'position': self.PLAYER_POSITIONS.get(player['pos']),
            'last_name': self._remove_emphasis(player['emphasis']['lastname']),
            'first_name': self._remove_emphasis(player['emphasis']['firstname']),
            'number': player['jn'],
            'khl_image_link': f"https://{player['image'].lstrip('/')}" if player['image'] else None,
            'captain': self.CAPTAIN_MAP.get(player['ca'])
        }

    def _transform_player_stats(self, stats: dict) -> dict:
        toi_sft = stats.pop('sft', '00:00(0)').rstrip(')').split('(')
        stats['toi'] = toi_sft[0]
        stats['sft'] = int(toi_sft[1]) if len(toi_sft) > 1 else None
        stats['tie'] = stats.pop('SFTE', '00:00(0)').split('(')[0]
        stats['tipp'] = stats.pop('SFTPP', '00:00(0)').split('(')[0]
        stats['tish'] = stats.pop('SFTSH', '00:00(0)').split('(')[0]
        stats['tien'] = stats.pop('SFTEN', '00:00(0)').split('(')[0]
        stats['avg_spd'] = stats.pop('as', None)
        stats['d'] = stats.pop('dt', None)
        stats['tka'] = stats.pop('fa', None)
        stats['hit'] = stats.pop('hits', None)
        stats['fo_pct'] = stats.pop('fow_pct', None)
        stats['pts'] = stats.get('g', 0) + stats.get('a', 0)
        stats['pintc'] = stats.pop('p_intc', None)
        stats['sog'] = stats.pop('shots', 0)
        stats['sog_pct'] = round(stats['g'] / stats['sog'] * 100, 2) if stats['sog'] > 0 else 0
        stats['toa'] = stats.pop('tiams', None)
        stats['ms'] = stats.pop('ts', None)
        for field in ['tie', 'tien', 'tish', 'tipp', 'toa', 'toi']:
            if field in stats and not stats[field]:
                stats[field] = "00:00"
        return stats

    def _transform_team_stats(self, stats: dict) -> dict:
        for k, v in {
            'hit': 'hits', 'pintc': 'p_intc', 'tka': 'fa', 'pls': 'gva', 'toa': 'tiams', 'tie': 'TIE', 'tien': 'TIEN',
            'ccd': 'contestedControlDuration', 'tish': 'TISH', 'tipp': 'TIPP', 'tcd': 'teamControlDuration',
            'd': 'distance'
        }.items():
            value = stats.pop(v, None)
            if not value and k in ['tie', 'tien', 'tish', 'tipp']:
                stats[k] = '00:00'
            else:
                stats[k] = value
        stats['sog'] = stats.pop('shots', 0)
        stats['sog_pct'] = round(stats['g'] / stats['sog'] * 100, 2) if stats['sog'] > 0 else 0
        stats.update({'pn': 0, 'shg': 0, 'ppg': 0})
        return stats

    def _aggregate_team_stats(self):
        self._extract_goals_and_reviews()
        self._extract_penalties()
        periods = self.home_team_stats.keys()
        for period in periods:
            home_data = self.home_team_stats[period]
            visitor_data = self.visitor_team_stats[period]
            visitor_data['contestedControlDuration'] = home_data.get('contestedControlDuration')
            self._transform_team_stats(home_data)
            self._transform_team_stats(visitor_data)

            home_g = home_data.get('g', 0)
            home_sog = home_data.get('sog', 0)
            visitor_g = visitor_data.get('g', 0)
            visitor_sog = visitor_data.get('sog', 0)
            home_data['sog_pct'] = round(home_g / home_sog * 100, 2) if home_sog > 0 else 0
            home_data['sv'] = visitor_sog - visitor_g
            home_data['sv_pct'] = round(home_data['sv'] / visitor_sog * 100, 2) if visitor_sog > 0 else None
            visitor_data['sog_pct'] = round(visitor_g / visitor_sog * 100, 2) if visitor_sog > 0 else 0
            visitor_data['sv'] = home_sog - home_g
            visitor_data['sv_pct'] = round(visitor_data['sv'] / home_sog * 100, 2) if home_sog > 0 else None

        for goal in self._goals:
            stat_obj = self.home_team_stats if goal.get('team_side') == 'A' else self.visitor_team_stats
            if goal['period'] in periods:
                if (pmg := goal.get('pmg', 0)) > 0:
                    stat_obj[goal.get('period')]['ppg'] += 1
                    stat_obj['total']['ppg'] += 1
                elif pmg < 0:
                    stat_obj[goal.get('period')]['shg'] += 1
                    stat_obj['total']['shg'] += 1

        for penalty in self.penalties:
            stat_obj = self.home_team_stats if penalty.get('team_side') == 'A' else self.visitor_team_stats
            stat_obj['total']['pn'] += 1
            stat_obj[penalty.get('period')]['pn'] += 1

    def _get_period_shortname(self, n: int) -> str:
        if n == 0:
            return 'total'
        elif 0 < n < 4:
            return str(n)
        else:
            ot_num = '' if n == 4 else str(n - 3)
            return 'ot' + ot_num

    def _remove_emphasis(self, s: str) -> str:
        return s.replace('&#769;', '')

    def dump(self):
        home_team_info, visitor_team_info = self.team_info
        home_lineup, visitor_lineup = self.lineup
        home_player_stats, visitor_player_stats = self.player_stats
        home_team_stats, visitor_team_stats = self.team_stats
        home_coach, visitor_coach = self.coaches
        return {
            'info': self.info,
            'referees': self.referees,
            'teams': {
                'home': {
                    'info': home_team_info,
                    'coach': home_coach,
                    'lineup': home_lineup,
                    'team_stats': home_team_stats,
                    'player_stats': home_player_stats
                },
                'visitor': {
                    'info': visitor_team_info,
                    'coach': visitor_coach,
                    'lineup': visitor_lineup,
                    'team_stats': visitor_team_stats,
                    'player_stats': visitor_player_stats
                }
            },
            'events': {
                'goals': self.goals,
                'video_reviews': self.video_reviews,
                'disallowed_goals': self.disallowed_goals,
                'penalties': self.penalties,
                'penalty_shots': self.penalty_shots,
                'shootouts': self.shootouts,
                'goalie_subs': self.goalie_subs
            }
        }
