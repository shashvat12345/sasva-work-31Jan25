from flask import Flask, render_template, request, redirect, url_for, session, flash 
from pymongo import MongoClient 
import logging 
 
# Set up logging 
logging.basicConfig(level=logging.INFO) 
 
app = Flask(__name__) 
app.secret_key = 'your_secret_key'  # Required for session management 
 
# MongoDB connection 
try: 
    client = MongoClient('localhost', 27017) 
    db = client['LoginInfo2']  # Create or use existing database 
    users_collection = db['users']  # Create or use existing collection 
    logging.info("MongoDB connection established successfully.") 
except Exception as e: 
    logging.error("Error connecting to MongoDB: %s", e, exc_info=True) 
 
@app.route('/') 
def home(): 
    logging.info("Home route accessed.") 
    return render_template('signin.html') 
 
@app.route('/signup', methods=['GET', 'POST']) 
def signup(): 
    if request.method == 'POST': 
        username = request.form['username'] 
        password = request.form['password'] 
        try: 
            # Check if the username already exists 
            if users_collection.find_one({'username': username}): 
                flash('Username already taken. Please choose a different one.', 'error') 
                logging.warning("Sign-up attempt with existing username: %s", username) 
            else: 
                users_collection.insert_one({'username': username, 'password': password}) 
                flash('Sign-up successful! Please sign in.', 'success') 
                logging.info("User signed up: %s", username) 
                return redirect(url_for('signin')) 
        except Exception as e: 
            logging.error("Error during sign-up: %s", e, exc_info=True) 
            flash('An error occurred during sign-up. Please try again.', 'error') 
    return render_template('signup.html') 
 
@app.route('/signin', methods=['GET', 'POST']) 
def signin(): 
    if request.method == 'POST': 
        username = request.form['username'] 
        password = request.form['password'] 
        user = users_collection.find_one({'username': username, 'password': password}) 
        if user: 
            session['username'] = username 
            flash('Welcome, ' + username + '!', 'success') 
            logging.info("User signed in: %s", username) 
            return redirect(url_for('welcome')) 
        else: 
            flash('Invalid credentials. Please try again.', 'error') 
            logging.warning("Invalid sign-in attempt for user: %s", username) 
    return render_template('signin.html') 
 
@app.route('/welcome') 
def welcome(): 
    if 'username' in session: 
        username = session['username'] 
        is_admin = username == 'admin'  # Check if the user is admin 
        logging.info("Welcome page accessed by user: %s", username) 
        return render_template('welcome.html', username=username, is_admin=is_admin) 
    return redirect(url_for('signin')) 
 
@app.route('/logout') 
def logout(): 
    session.pop('username', None) 
    flash('You have been logged out.', 'info') 
    logging.info("User logged out.") 
    return redirect(url_for('signin')) 
 
@app.route('/view_users') 
def view_users(): 
    if 'username' in session and session['username'] == 'admin': 
        try: 
            users = users_collection.find()  # Retrieve all users 
            logging.info("User list accessed by admin.") 
            return render_template('view_users.html', users=users) 
        except Exception as e: 
            logging.error("Error retrieving user list: %s", e, exc_info=True) 
            flash('An error occurred while retrieving users. Please try again.', 'error') 
            return redirect(url_for('welcome')) 
    else: 
        flash('Access denied. You must be an admin to view this page.', 'error') 
        return redirect(url_for('signin')) 
 
@app.route('/delete_users', methods=['POST']) 
def delete_users(): 
    if 'username' in session and session['username'] == 'admin': 
        usernames_to_delete = request.form.getlist('usernames')  # Get list of selected usernames 
        try: 
            result = users_collection.delete_many({'username': {'$in': usernames_to_delete}}) 
            if result.deleted_count > 0: 
                flash(f'Successfully deleted {result.deleted_count} user(s).', 'success') 
                logging.info("Deleted %d user(s): %s", result.deleted_count, usernames_to_delete) 
            else: 
                flash('No users were deleted. Please check your selection.', 'info') 
                logging.info("No users deleted for usernames: %s", usernames_to_delete) 
        except Exception as e: 
            logging.error("Error during user deletion: %s", e, exc_info=True) 
            flash('An error occurred while deleting users. Please try again.', 'error') 
    else: 
        flash('Access denied. You must be an admin to perform this action.', 'error') 
    return redirect(url_for('view_users')) 
 
if __name__ == '__main__': 
    app.run(port=8000)  # Use port 8000 instead of 5000