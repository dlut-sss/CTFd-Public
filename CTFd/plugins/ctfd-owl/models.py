from CTFd.models import (
    db,
    Challenges,
)
import datetime


class DynamicCheckChallenge(Challenges):
    __tablename__ = 'dynamic_docker_compose'
    __mapper_args__ = {"polymorphic_identity": "dynamic_docker_compose"}
    id = db.Column(None, db.ForeignKey("challenges.id",
                                       ondelete="CASCADE"), primary_key=True)

    # deployments settings
    deployment = db.Column(db.String(32))
    dirname = db.Column(db.String(80))

    dynamic_score = db.Column(db.Integer, default=0)
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)

    # frp settings
    redirect_type = db.Column(db.Text, default="direct")
    redirect_port = db.Column(db.Integer, default=80)
    function = db.Column(db.String(32), default="logarithmic")

    def __init__(self, *args, **kwargs):
        super(DynamicCheckChallenge, self).__init__(**kwargs)
        self.initial = kwargs["value"]


class OwlContainers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))
    docker_id = db.Column(db.String(32))
    ip = db.Column(db.String(32))
    port = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    renew_count = db.Column(db.Integer, nullable=False, default=0)
    flag = db.Column(db.String(128), nullable=False)

    # Relationships
    user = db.relationship("Users", foreign_keys="OwlContainers.user_id", lazy="select")
    challenge = db.relationship(
        "Challenges", foreign_keys="OwlContainers.challenge_id", lazy="select"
    )

    def __init__(self, *args, **kwargs):
        super(OwlContainers, self).__init__(**kwargs)
