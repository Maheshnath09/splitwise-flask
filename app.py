from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import and_, or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///splitwise.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
# Association table for friends relationship
friends = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    expenses = db.relationship('Expense', backref='payer', lazy=True, foreign_keys='Expense.payer_id')
    
    # Friends relationship (self-referential many-to-many)
    friends = db.relationship(
        'User',
        secondary=friends,
        primaryjoin=(friends.c.user_id == id),
        secondaryjoin=(friends.c.friend_id == id),
        backref=db.backref('friend_of', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # Groups relationship
    groups = db.relationship('GroupMember', back_populates='user')
    
    def add_friend(self, user):
        if not self.is_friends_with(user):
            self.friends.append(user)
            user.friends.append(self)
            db.session.commit()
            return True
        return False
        
    def remove_friend(self, user):
        if self.is_friends_with(user):
            self.friends.remove(user)
            user.friends.remove(self)
            db.session.commit()
            return True
        return False
        
    def is_friends_with(self, user):
        return self.friends.filter(User.id == user.id).count() > 0

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    members = db.relationship('GroupMember', back_populates='group')
    expenses = db.relationship('Expense', back_populates='group')

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    group = db.relationship('Group', back_populates='members')
    user = db.relationship('User', back_populates='groups')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    
    # Relationships
    group = db.relationship('Group', back_populates='expenses')
    splits = db.relationship('ExpenseSplit', back_populates='expense', cascade='all, delete-orphan')
    
    def split_equally(self, users):
        split_amount = round(self.amount / (len(users) + 1), 2)  # +1 for the payer
        for user in users:
            if user.id != self.payer_id:  # Don't create a split for the payer
                split = ExpenseSplit(
                    expense_id=self.id,
                    user_id=user.id,
                    amount=split_amount,
                    is_settled=False
                )
                db.session.add(split)

class ExpenseSplit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_settled = db.Column(db.Boolean, default=False)
    settled_at = db.Column(db.DateTime)
    
    # Relationships
    expense = db.relationship('Expense', back_populates='splits')
    user = db.relationship('User')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's expenses and balances
    expenses = Expense.query.filter(Expense.payer_id == current_user.id).order_by(Expense.date.desc()).all()
    
    # Calculate balances with friends
    balances = {}
    
    # Get all expenses where user is involved
    involved_expenses = db.session.query(Expense).join(
        ExpenseSplit, Expense.id == ExpenseSplit.expense_id
    ).filter(
        or_(
            Expense.payer_id == current_user.id,
            ExpenseSplit.user_id == current_user.id
        )
    ).all()
    
    # Calculate net balance with each friend
    for friend in current_user.friends:
        balance = 0.0
        # Amounts user owes to friend
        user_owes = db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(
            Expense, Expense.id == ExpenseSplit.expense_id
        ).filter(
            Expense.payer_id == friend.id,
            ExpenseSplit.user_id == current_user.id,
            ExpenseSplit.is_settled == False
        ).scalar() or 0.0
        
        # Amounts friend owes to user
        friend_owes = db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(
            Expense, Expense.id == ExpenseSplit.expense_id
        ).filter(
            Expense.payer_id == current_user.id,
            ExpenseSplit.user_id == friend.id,
            ExpenseSplit.is_settled == False
        ).scalar() or 0.0
        
        net_balance = round(friend_owes - user_owes, 2)
        if net_balance != 0:
            balances[friend] = net_balance
    
    # Get recent activity
    recent_activity = db.session.query(Expense).filter(
        or_(
            Expense.payer_id == current_user.id,
            Expense.id.in_(
                db.session.query(ExpenseSplit.expense_id).filter(
                    ExpenseSplit.user_id == current_user.id
                )
            )
        )
    ).order_by(Expense.date.desc()).limit(10).all()
    
    # Get groups
    groups = Group.query.join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    
    return render_template('dashboard.html', 
                         expenses=expenses[:5],  # Only show 5 most recent expenses
                         balances=balances,
                         recent_activity=recent_activity,
                         groups=groups)

# In app.py, update the add_expense route
@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        split_type = request.form.get('split_type', 'you_paid')
        friend_ids = request.form.getlist('friend_ids')
        group_id = request.form.get('group_id')
        
        # Create expense
        expense = Expense(
            description=description,
            amount=amount,
            payer_id=current_user.id,
            group_id=group_id if group_id != 'none' else None
        )
        
        # Add to database first to get the expense ID
        db.session.add(expense)
        db.session.commit()
        
        # Handle splits
        if split_type == 'you_paid':
            # Split equally among selected friends
            split_amount = amount / (len(friend_ids) + 1)  # +1 for yourself
            for friend_id in friend_ids:
                split = ExpenseSplit(
                    expense_id=expense.id,
                    user_id=friend_id,
                    amount=split_amount
                )
                db.session.add(split)
        else:
            # Someone else paid, current user owes the full amount
            split = ExpenseSplit(
                expense_id=expense.id,
                user_id=current_user.id,
                amount=amount
            )
            db.session.add(split)
        
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # For GET request
    friends = current_user.friends.all()
    groups = Group.query.join(GroupMember).filter(
        GroupMember.user_id == current_user.id
    ).all()
    
    return render_template('add_expense.html', 
                         friends=friends,
                         groups=groups)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Friend routes
# In app.py, update the friends route
@app.route('/friends')
@login_required
def friends():
    # Get all users who are not the current user and not already friends
    current_friend_ids = [friend.id for friend in current_user.friends.all()]
    non_friends = User.query.filter(
        User.id != current_user.id,
        ~User.id.in_(current_friend_ids)
    ).all()
    
    return render_template('friends.html', 
                         friends=current_user.friends.all(),
                         non_friends=non_friends)

@app.route('/add_friend/<int:friend_id>', methods=['POST'])
@login_required
def add_friend(friend_id):
    friend = User.query.get_or_404(friend_id)
    if current_user.add_friend(friend):
        db.session.commit()
        flash(f'You are now friends with {friend.username}!', 'success')
    else:
        flash(f'You are already friends with {friend.username}.', 'info')
    return redirect(url_for('friends'))

@app.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    friend = User.query.get_or_404(friend_id)
    if current_user.remove_friend(friend):
        db.session.commit()
        flash(f'Removed {friend.username} from your friends.', 'info')
    return redirect(url_for('friends'))

# Group routes
@app.route('/groups')
@login_required
def groups():
    groups = Group.query.join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    return render_template('groups.html', groups=groups)

# In app.py, update the create_group route
@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        friend_ids = request.form.getlist('friend_ids')
        
        # Create group
        group = Group(
            name=name,
            created_by=current_user.id
        )
        db.session.add(group)
        db.session.commit()
        
        # Add creator as member
        creator_member = GroupMember(
            group_id=group.id,
            user_id=current_user.id
        )
        db.session.add(creator_member)
        
        # Add selected friends
        for friend_id in friend_ids:
            member = GroupMember(
                group_id=group.id,
                user_id=friend_id
            )
            db.session.add(member)
        
        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('groups'))
    
    friends = current_user.friends.all()
    return render_template('create_group.html', friends=friends)


    # In app.py, add this new route
@app.route('/group/<int:group_id>/add_member', methods=['POST'])
@login_required
def add_group_member(group_id):
    group = Group.query.get_or_404(group_id)
    if group.created_by != current_user.id:
        flash('Only group creator can add members', 'danger')
        return redirect(url_for('view_group', group_id=group_id))
    
    friend_id = request.form.get('friend_id')
    if not friend_id:
        flash('Please select a friend to add', 'danger')
        return redirect(url_for('view_group', group_id=group_id))
    
    # Check if already a member
    existing = GroupMember.query.filter_by(
        group_id=group_id,
        user_id=friend_id
    ).first()
    
    if not existing:
        member = GroupMember(
            group_id=group_id,
            user_id=friend_id
        )
        db.session.add(member)
        db.session.commit()
        flash('Member added to group!', 'success')
    else:
        flash('This user is already in the group', 'info')
    
    return redirect(url_for('view_group', group_id=group_id))

@app.route('/groups/<int:group_id>')
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Check if current user is a member of the group
    if not any(member.user_id == current_user.id for member in group.members):
        flash('You are not a member of this group', 'error')
        return redirect(url_for('groups'))
    
    # Get group expenses with splits
    expenses = Expense.query.filter_by(group_id=group_id).order_by(Expense.date.desc()).all()
    
    # Calculate balances within the group
    balances = {}
    for member in group.members:
        # Amounts user owes to this member
        user_owes = db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(
            Expense, Expense.id == ExpenseSplit.expense_id
        ).filter(
            Expense.payer_id == member.user_id,
            ExpenseSplit.user_id == current_user.id,
            Expense.group_id == group_id,
            ExpenseSplit.is_settled == False
        ).scalar() or 0.0
        
        # Amounts this member owes to user
        member_owes = db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(
            Expense, Expense.id == ExpenseSplit.expense_id
        ).filter(
            Expense.payer_id == current_user.id,
            ExpenseSplit.user_id == member.user_id,
            Expense.group_id == group_id,
            ExpenseSplit.is_settled == False
        ).scalar() or 0.0
        
        net_balance = round(member_owes - user_owes, 2)
        if member.user_id != current_user.id and net_balance != 0:
            balances[member.user] = net_balance
    
    return render_template('view_group.html', 
                         group=group, 
                         expenses=expenses,
                         balances=balances)

# Settle up
@app.route('/settle_up', methods=['POST'])
@login_required
def settle_up():
    expense_id = request.form.get('expense_id')
    friend_id = request.form.get('friend_id')
    
    if expense_id:
        # Settle a specific expense
        split = ExpenseSplit.query.filter_by(
            expense_id=expense_id,
            user_id=current_user.id,
            is_settled=False
        ).first_or_404()
        
        split.is_settled = True
        split.settled_at = datetime.utcnow()
        db.session.commit()
        
        flash('Expense marked as settled!', 'success')
    elif friend_id:
        # Settle all debts with a friend
        # Get all unsettled splits between current user and friend
        splits = db.session.query(ExpenseSplit).join(
            Expense, Expense.id == ExpenseSplit.expense_id
        ).filter(
            or_(
                and_(
                    Expense.payer_id == current_user.id,
                    ExpenseSplit.user_id == friend_id
                ),
                and_(
                    Expense.payer_id == friend_id,
                    ExpenseSplit.user_id == current_user.id
                )
            ),
            ExpenseSplit.is_settled == False
        ).all()
        
        for split in splits:
            split.is_settled = True
            split.settled_at = datetime.utcnow()
        
        db.session.commit()
        friend = User.query.get(friend_id)
        flash(f'All debts with {friend.username} have been settled!', 'success')
    
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/debug/users')
def debug_users():
    users = User.query.all()
    return '<br>'.join([f"{u.id}: {u.username} ({u.email})" for u in users])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
