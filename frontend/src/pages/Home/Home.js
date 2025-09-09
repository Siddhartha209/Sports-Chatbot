import React, { useState } from "react";
import "./Home.css";

const Home = () => {
  const [showSignup, setShowSignup] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [step, setStep] = useState(1); // 1 = signup form, 2 = 2FA step

  // --- SIGNUP ---
  const handleSignupClick = () => {
    setShowSignup(true);
    setStep(1);
  };

  const handleCloseSignup = () => {
    setShowSignup(false);
    setStep(1);
  };

  const handleSubmitSignup = (e) => {
    e.preventDefault();
    setStep(2); // move to 2FA
  };

  const handleVerify2FA = (e) => {
    e.preventDefault();
    alert("Signup successful ✅");
    setShowSignup(false);
    setStep(1);
  };

  // --- LOGIN ---
  const handleLoginClick = () => {
    setShowLogin(true);
  };

  const handleCloseLogin = () => {
    setShowLogin(false);
  };

  const handleSubmitLogin = (e) => {
    e.preventDefault();
    // Normally check credentials with backend
    alert("Login successful ✅");
    setShowLogin(false);
  };

  return (
    <div className="home-page">
      {/* Logo */}
      <img src="/img/web_logo.png" alt="Sports Hub Logo" className="logo" />

      {/* Buttons */}
      <div className="button-group">
        <button className="login-btn" onClick={handleLoginClick}>
          Login
        </button>
        <button className="signup-btn" onClick={handleSignupClick}>
          Sign Up
        </button>
      </div>

      {/* Info Section */}
      <p className="info">Welcome to Sports Hub Chatbot!

        Sports Hub is your all-in-one platform for sports fans to get instant answers. 
        Simply sign up or log in to start chatting with our AI-powered sports assistant, ask questions 
        about Premier League players, UFC fighters, and more.
        **How it works:**
        - Create an account or log in securely (with email and password, plus 2FA verification) [Optional].
        - Use the chatbot to ask anything about Premier League Player stats:  
          - Goals  
          - Assists  
          - Shots
          - Fouls  
          - And more!
        - For UFC fans, inquire about fighters, match histories, and upcoming events. (in progress)
        - Switch between dark and light mode for your preferred viewing experience.
        - Navigate using the sidebar to explore more features.
        - Don't forget to clear your chat history anytime for a fresh start!
        Get started now and join the conversation!</p>

      {/* --- Signup Modal --- */}
      {showSignup && (
        <div className="modal-overlay">
          <div className="modal">
            {step === 1 && (
              <>
                <h2>Create Account</h2>
                <form className="signup-form" onSubmit={handleSubmitSignup}>
                  <label>
                    First Name:
                    <input type="text" name="firstName" required />
                  </label>
                  <label>
                    Date of Birth:
                    <input type="date" name="dob" required />
                  </label>
                  <label>
                    Email:
                    <input type="email" name="email" required />
                  </label>
                  <label>
                    Password:
                    <input type="password" name="password" required />
                  </label>
                  <div className="modal-buttons">
                    <button type="submit" className="signup-btn">
                      Sign Up
                    </button>
                    <button type="button" className="close-btn" onClick={handleCloseSignup}>
                      Close
                    </button>
                  </div>
                </form>
              </>
            )}

            {step === 2 && (
              <>
                <h2>Email Verification</h2>
                <form className="signup-form" onSubmit={handleVerify2FA}>
                  <p>Please enter the 2FA code sent to your email.</p>
                  <label>
                    2FA Code:
                    <input type="text" name="twofa" required />
                  </label>
                  <div className="modal-buttons">
                    <button type="submit" className="signup-btn">
                      Verify
                    </button>
                    <button type="button" className="close-btn" onClick={handleCloseSignup}>
                      Cancel
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}

      {/* --- Login Modal --- */}
      {showLogin && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Login</h2>
            <form className="signup-form" onSubmit={handleSubmitLogin}>
              <label>
                Email:
                <input type="text" name="username" required />
              </label>
              <label>
                Password:
                <input type="password" name="password" required />
              </label>
              <div className="modal-buttons">
                <button type="submit" className="login-btn">
                  Login
                </button>
                <button type="button" className="close-btn" onClick={handleCloseLogin}>
                  Close
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;
