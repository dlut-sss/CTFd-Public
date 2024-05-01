import datetime
from collections import defaultdict
from decimal import Decimal
from functools import wraps

from flask import (
    render_template,
    Blueprint,
    url_for,
    redirect,
    request
)
from sqlalchemy.sql import or_

import CTFd.utils.scores
from CTFd import utils
from CTFd.models import db, Solves, Challenges, Users, Teams, Awards
from CTFd.plugins import (
    register_admin_plugin_menu_bar,
)
from CTFd.utils import get_config, set_config
from CTFd.utils.config import is_scoreboard_frozen, ctf_theme, is_users_mode
from CTFd.utils.config.visibility import challenges_visible, scores_visible
from CTFd.utils.dates import (
    ctf_started, ctftime, view_after_ctf, unix_time_to_utc
)
from CTFd.utils.decorators import admins_only
from CTFd.utils.helpers import get_infos
from CTFd.utils.modes import TEAMS_MODE
from CTFd.utils.user import is_admin, authed

categories = []


def setup_default_configs():
    current_year = datetime.datetime.now().year
    year_string = str(current_year)
    for key, val in {
        'setup': 'true',
        'switch': False,
        'score_switch': False,
        'score_grade': year_string,
        'score_num': 1200,
    }.items():
        set_config('matrix:' + key, val)


def load(app):
    plugin_name = __name__.split('.')[-1]
    set_config('matrix:plugin_name', plugin_name)
    app.db.create_all()
    if not get_config("matrix:setup"):
        setup_default_configs()
    if not get_config("matrix:score_switch"):
        set_config("matrix:score_switch", False)
    if not get_config("matrix:score_grade"):
        current_year = datetime.datetime.now().year
        year_string = str(current_year)
        set_config("matrix:score_grade", year_string)
    if not get_config("matrix:score_num"):
        set_config("matrix:score_num", 1200)
    register_admin_plugin_menu_bar(title='Matrix',
                                   route='/plugins/matrix/admin/settings')

    page_blueprint = Blueprint("matrix",
                               __name__,
                               template_folder="templates",
                               static_folder="static",
                               url_prefix="/plugins/matrix")
    worker_config_commit = None

    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_configs():
        nonlocal worker_config_commit
        # 处理GET请求
        if not get_config("matrix:switch") != worker_config_commit:
            worker_config_commit = get_config("matrix:switch")
        return render_template('matrix_config.html')

    app.register_blueprint(page_blueprint)

    def get_score_by_challenge_id(challenges, challenge_id):
        for challenge in challenges:
            if challenge.id == challenge_id:
                return challenge.value
        return None

    # @cache.memoize(timeout=60)
    def get_matrix_standings():
        # 获取所有题目数据并获取数目
        challenges = Challenges.query.filter(*[]).order_by(Challenges.id.asc()).all()
        # 获取所有分数数据和解题数据，并过滤无效数据
        solves = db.session.query(Solves.date.label('date'),
                                  Solves.challenge_id.label('challenge_id'),
                                  Solves.user_id.label('user_id'),
                                  Solves.team_id.label('team_id')).all()
        awards = db.session.query(Awards.user_id.label('user_id'),
                                  Awards.team_id.label('team_id'),
                                  Awards.value.label('value'),
                                  Awards.date.label('date')).all()
        teams = db.session.query(Teams.id.label('team_id'),
                                 Teams.name.label('name'),
                                 Teams.hidden.label('hidden'),
                                 Teams.banned.label('banned')).all()
        users = db.session.query(Users.id.label('user_id'),
                                 Users.name.label('name'),
                                 Users.sid.label('sid'),
                                 Users.hidden.label('hidden'),
                                 Users.banned.label('banned')).all()
        freeze = utils.get_config('freeze')
        mode = get_config("user_mode")
        if freeze:
            freeze = unix_time_to_utc(freeze)
            solves = [solve for solve in solves if solve.date < freeze]
            awards = [award for award in awards if award.date < freeze]
        # 创建一个字典来存储每个challenge_id的前三条数据
        top_solves = defaultdict(list)
        # 将solves数据按照challenge_id和date排序
        sorted_solves = sorted(solves, key=lambda x: (x.challenge_id, x.date))
        # 遍历排序后的solves数据
        for solve in sorted_solves:
            challenge_id = solve.challenge_id
            # 检查是否已经存储了三条数据，如果是，跳过
            if len(top_solves[challenge_id]) >= 3:
                continue
            # 检查是否隐藏/封禁
            user = next((user for user in users if user.user_id == solve.user_id), None)
            if not user:
                continue
            if user.hidden or user.banned:
                continue

            if mode == TEAMS_MODE:
                team = next((team for team in teams if team.team_id == solve.team_id), None)
                if not team:
                    continue
                if team.hidden or team.banned:
                    continue

            # 否则将数据添加到对应的challenge_id中
            top_solves[challenge_id].append({
                'date': solve.date,
                'user_id': solve.user_id,
                'team_id': solve.team_id
            })
        if mode == TEAMS_MODE:
            matrix_scores = []
            for team in teams:
                if team.hidden or team.banned:
                    continue
                team_solves = [solve for solve in solves if solve[3] == team.team_id]
                total_score = 0
                team_status = []
                for solve in team_solves:
                    challenge_id = solve[1]
                    rank = 4
                    for index, top_solve in enumerate(top_solves[challenge_id]):
                        if top_solve['team_id'] == team.team_id:
                            rank = index + 1
                    # 按血加分
                    score = get_score_by_challenge_id(challenges, challenge_id)
                    if rank == 1:
                        score *= Decimal('1.1')
                    elif rank == 2:
                        score *= Decimal('1.05')
                    elif rank == 3:
                        score *= Decimal('1.03')
                    total_score += score

                    # 记录解决状态和排名
                    team_status.append({'challenge_id': challenge_id, 'rank': rank})

                award_value = 0
                # 奖项加分
                for award in awards:
                    if award.team_id == team.team_id:
                        total_score += award.value
                        award_value += award.value

                matrix_scores.append(
                    {'name': team.name, 'id': team.team_id, 'total_score': total_score,
                     'challenge_solved': team_status, 'award_value': award_value})
            matrix_scores.sort(key=lambda x: x['total_score'], reverse=True)
            return matrix_scores
        else:
            matrix_scores = []
            for user in users:
                if user.hidden or user.banned:
                    continue
                user_solves = [solve for solve in solves if solve[2] == user.user_id]
                total_score = 0
                user_status = []
                for solve in user_solves:
                    challenge_id = solve[1]
                    rank = 4
                    for index, top_solve in enumerate(top_solves[challenge_id]):
                        if top_solve['user_id'] == user.user_id:
                            rank = index + 1
                    # 按血加分
                    score = get_score_by_challenge_id(challenges, challenge_id)
                    if rank == 1:
                        score *= Decimal('1.1')
                    elif rank == 2:
                        score *= Decimal('1.05')
                    elif rank == 3:
                        score *= Decimal('1.03')
                    total_score += score

                    # 记录解决状态和排名
                    user_status.append({'challenge_id': challenge_id, 'rank': rank})
                award_value = 0
                # 新生加分
                if get_config("matrix:score_switch"):
                    if user.sid:
                        if str(user.sid[:4]) in str(get_config("matrix:score_grade")):
                            total_score += get_config("matrix:score_num")
                            award_value += get_config("matrix:score_num")
                # 奖项加分
                for award in awards:
                    if award.user_id == user.user_id:
                        total_score += award.value
                        award_value += award.value

                matrix_scores.append(
                    {'name': user.name, 'id': user.user_id, 'total_score': total_score,
                     'challenge_solved': user_status, 'award_value': award_value})
            matrix_scores.sort(key=lambda x: x['total_score'], reverse=True)
            return matrix_scores

    def get_challenges():
        global categories
        categories = []
        if not is_admin():
            if not ctftime():
                if view_after_ctf():
                    pass
                else:
                    return []
        if challenges_visible() and (ctf_started() or is_admin()):
            challenges = db.session.query(
                Challenges.id,
                Challenges.name,
                Challenges.category,
                Challenges.value
            ).filter(or_(Challenges.state != 'hidden', Challenges.state is None)).order_by(
                Challenges.category.asc()).all()
            category_counts = defaultdict(int)
            challenges_list = []
            for x in challenges:
                challenges_list.append({
                    'id': x.id,
                    'name': x.name,
                    'category': x.category.upper(),
                    'value': x.value,
                })
                category_counts[x.category.upper()] += 1
            for category, count in category_counts.items():
                categories.append({
                    'category': category.upper(),
                    'count': count
                })
            categories = sorted(categories, key=lambda x: x['category'])
            return challenges_list
        return []

    def matrix_user_get_score(self, admin=False):
        from CTFd.utils.modes import USERS_MODE
        import traceback
        try:
            # 获取所有题目数据并获取数目
            challenges = Challenges.query.filter(*[]).order_by(Challenges.id.asc()).all()
            # 获取所有分数数据和解题数据，并过滤无效数据
            solves = db.session.query(Solves.date.label('date'), Solves.challenge_id.label('challenge_id'),
                                      Solves.user_id.label('user_id')).all()
            award_score = db.func.sum(Awards.value).label("award_score")
            award = db.session.query(award_score).filter_by(user_id=self.id)
            if not admin:
                freeze = utils.get_config('freeze')
                if freeze:
                    freeze = unix_time_to_utc(freeze)
                    solves = [solve for solve in solves if solve.date < freeze]
                    award = award.filter(Awards.date < freeze)
            # 创建一个字典来存储每个challenge_id的前三条数据
            top_solves = defaultdict(list)
            # 将solves数据按照challenge_id和date排序
            sorted_solves = sorted(solves, key=lambda x: (x.challenge_id, x.date))
            # 遍历排序后的solves数据
            for solve in sorted_solves:
                challenge_id = solve.challenge_id
                # 检查是否已经存储了三条数据，如果是，跳过
                if len(top_solves[challenge_id]) >= 3:
                    continue
                # 否则将数据添加到对应的challenge_id中
                top_solves[challenge_id].append({
                    'date': solve.date,
                    'user_id': solve.user_id
                })
            user_solves = [solve for solve in solves if solve[2] == self.id]
            total_score = 0
            for solve in user_solves:
                challenge_id = solve[1]
                rank = 4
                for index, top_solve in enumerate(top_solves[challenge_id]):
                    if top_solve['user_id'] == self.id:
                        rank = index + 1
                # 按血加分
                score = self.get_score_by_challenge_id(challenges, challenge_id)
                if rank == 1:
                    score *= Decimal('1.1')
                elif rank == 2:
                    score *= Decimal('1.05')
                elif rank == 3:
                    score *= Decimal('1.03')

                total_score += score

            # 新生加分
            mode = get_config("user_mode")
            if mode == USERS_MODE:
                if get_config("matrix:score_switch"):
                    if self.sid:
                        if str(self.sid[:4]) in str(get_config("matrix:score_grade")):
                            total_score += get_config("matrix:score_num")

            # 奖项加分
            award = award.first()
            if award:
                total_score += int(award.award_score or 0)

            return total_score
        except Exception as e:
            print(e, flush=True)
            print(''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True)
            return 0

    def set_matrix_user_score_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if get_config("matrix:switch"):
                return matrix_user_get_score(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    CTFd.models.Users.get_score = set_matrix_user_score_wrapper(CTFd.models.Users.get_score)

    def color_hash(text):
        hash_value = 0
        for char in text:
            hash_value = ord(char) + ((hash_value << 5) - hash_value)
            hash_value = hash_value & hash_value

        # 计算HSL值
        h = ((hash_value % 360) + 360) % 360
        s = (((hash_value % 25) + 25) % 25) + 75
        l = (((hash_value % 20) + 20) % 20) + 40

        return f'hsl({h}, {s}%, {l}%)'

    def scoreboard_view():
        language = request.cookies.get("Scr1wCTFdLanguage", "zh")
        if scores_visible() and not authed():
            return redirect(url_for('auth.login', next=request.path))
        if get_config("matrix:switch"):
            if language == "zh":
                if not scores_visible():
                    return render_template('scoreboard-matrix.html',
                                           errors=['当前分数已隐藏'])
                if not ctf_started():
                    return render_template('scoreboard-matrix.html',
                                           errors=['比赛尚未开始'])
            else:
                if not scores_visible():
                    return render_template('scoreboard-matrix.html',
                                           errors=['Score is currently hidden'])
                if not ctf_started():
                    return render_template('scoreboard-matrix.html',
                                           errors=['Not Start Yet'])
            standings = get_matrix_standings()
            return render_template('scoreboard-matrix.html',
                                   standings=standings,
                                   score_frozen=is_scoreboard_frozen(),
                                   mode='users' if is_users_mode() else 'teams',
                                   challenges=get_challenges(),
                                   categories=categories,
                                   theme=ctf_theme())
        else:
            freeze = get_config("freeze")
            infos = get_infos()
            if language == "zh":
                if freeze:
                    infos.append("计分板已经冻结。")
                if not scores_visible():
                    infos.append("当前分数已隐藏。")
                if not ctf_started():
                    infos.append("比赛尚未开始。")
                    return render_template("scoreboard.html", infos=infos)
            else:
                if freeze:
                    infos.append("Scoreboard is frozen")
                if not scores_visible():
                    infos.append("Score is currently hidden")
                if not ctf_started():
                    infos.append("Not Start Yet")
                    return render_template("scoreboard.html", infos=infos)

            return render_template("scoreboard.html", standings=CTFd.utils.scores.get_standings(), infos=infos)

    app.view_functions['scoreboard.listing'] = scoreboard_view
    app.add_template_global(color_hash, 'color_hash')
