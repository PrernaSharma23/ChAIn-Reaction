import React, { useState } from "react";
import "./LoginPage.scss";
import { loginUser } from "../../services/authService";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
    const navigate = useNavigate();

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleLogin = () => {
        const success = loginUser(username, password);

        if (success) {
            navigate("/dashboard");
        } else {
            setError("Invalid username or password");
        }
    };

    return (
        <div className="login-container">
            <div className="login-wrapper">
                <div className="login-left">
                    <h2 className="login-title">Login</h2>
                    <p className="login-subtitle">Sign In to your account</p>

                    <label className="input-label">Username</label>
                    <div className="input-wrapper">
                        <span className="input-icon">👤</span>
                        <input type="text" className="input-field" value={username}
                            onChange={(e) => setUsername(e.target.value)} />
                    </div>

                    <label className="input-label">Password</label>
                    <div className="input-wrapper">
                        <span className="input-icon">🔒</span>
                        <input type="password" className="input-field" value={password}
              onChange={(e) => setPassword(e.target.value)} />
                    </div>

                    {error && <p style={{ color: "red", marginTop: "10px" }}>{error}</p>}

                    <button className="login-btn" onClick={handleLogin}>Login</button>
                </div>

                <div className="login-right">
                    {/* Dependency-Track style logo (SVG) */}
                    <svg
                        className="logo-svg"
                        viewBox="0 0 200 200"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <defs>
                            <mask id="logo-cutout">
                                <rect width="100%" height="100%" fill="white" />
                                <rect x="80" y="80" width="40" height="40" rx="10" fill="black" />
                            </mask>
                        </defs>

                        <g fill="#2da4ff" mask="url(#logo-cutout)">
                            <rect x="80" y="0" width="40" height="70" />
                            <rect x="80" y="130" width="40" height="70" />
                            <rect x="140" y="70" width="60" height="40" />
                            <rect x="0" y="90" width="60" height="40" />
                            <rect x="0" y="150" width="60" height="40" />
                            <rect x="140" y="10" width="60" height="40" />
                        </g>
                    </svg>

                    <h1 className="brand-text">
                        chAIn- <span>reaction</span>
                    </h1>
                </div>
            </div>
        </div>
    );
}
