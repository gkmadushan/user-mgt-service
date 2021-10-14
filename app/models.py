from sqlalchemy import Column, ForeignKey, DateTime, SmallInteger, String, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref


Base = declarative_base()
metadata = Base.metadata

t_user_group = Table(
    'user_group', metadata,
    Column('group_id', ForeignKey('group.id'), primary_key=True, nullable=False),
    Column('user_id', ForeignKey('user.id'), primary_key=True, nullable=False)
)

class Group(Base):
    __tablename__ = 'group'

    id = Column(UUID, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)
    description = Column(String(6000))

    users = relationship('User', secondary=t_user_group, back_populates="groups")


class Role(Base):
    __tablename__ = 'role'

    id = Column(UUID, primary_key=True)
    code = Column(String(250), nullable=False, unique=True)
    name = Column(String(250), nullable=False)


class User(Base):
    __tablename__ = 'user'

    id = Column(UUID, primary_key=True)
    email = Column(String(250), unique=True)
    password = Column(String(250))
    name = Column(String(250))
    secret = Column(String(250))
    deleted = Column(SmallInteger)
    created_by = Column(ForeignKey('user.id'))
    deleted_by = Column(ForeignKey('user.id'))
    role_id = Column(ForeignKey('role.id'), nullable=False)
    active = Column(SmallInteger, nullable=False, server_default=text("0"))
    created_at = Column(DateTime, server_default=text("now()"))

    parent = relationship('User', remote_side=[id], primaryjoin='User.created_by == User.id')
    parent1 = relationship('User', remote_side=[id], primaryjoin='User.deleted_by == User.id')
    role = relationship('Role')

    groups = relationship('Group', secondary=t_user_group, back_populates="users")


class OnetimeToken(Base):
    __tablename__ = 'onetime_token'

    id = Column(UUID, primary_key=True)
    otp = Column(String(255))
    created_at = Column(DateTime)
    user_id = Column(ForeignKey('user.id'), nullable=False)
    active = Column(SmallInteger, nullable=False, server_default=text("0"))

    user = relationship('User')

