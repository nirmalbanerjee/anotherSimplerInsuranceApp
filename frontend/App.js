// ...existing code...
import React, { useState, useEffect } from "react";
// ...existing code...

import React, { useState, useEffect } from "react";

const API = "http://localhost:8000";

function App() {
  const [token, setToken] = useState("");
  const [role, setRole] = useState("");
  const [username, setUsername] = useState("");
  const [policies, setPolicies] = useState([]);
  const [form, setForm] = useState({ name: "", details: "" });
  const [authForm, setAuthForm] = useState({ username: "", password: "", role: "user" });
  const [isLogin, setIsLogin] = useState(true);

  useEffect(() => {
    if (token) fetchPolicies();
  }, [token]);

  function handleAuth(e) {
    e.preventDefault();
    fetch(`${API}/${isLogin ? "login" : "register"}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: isLogin
        ? new URLSearchParams(authForm).toString()
        : JSON.stringify(authForm),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.access_token) {
          setToken(data.access_token);
          setUsername(authForm.username);
          setRole(authForm.role);
        }
      });
  }

  function fetchPolicies() {
    fetch(`${API}/policies`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then(setPolicies);
  }

  function handleCreate(e) {
    e.preventDefault();
    fetch(`${API}/policies`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(form),
    })
      .then((r) => r.json())
      .then((p) => setPolicies([...policies, p]));
  }

  function handleDelete(id) {
    fetch(`${API}/policies/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }).then(() => setPolicies(policies.filter((p) => p.id !== id)));
  }

  return (
    <div style={{ maxWidth: 400, margin: "auto" }}>
      {!token ? (
        <form onSubmit={handleAuth}>
          <h2>{isLogin ? "Login" : "Register"}</h2>
          <input
            placeholder="Username"
            value={authForm.username}
            onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={authForm.password}
            onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
            required
          />
          {!isLogin && (
            <select
              value={authForm.role}
              onChange={(e) => setAuthForm({ ...authForm, role: e.target.value })}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          )}
          <button type="submit">{isLogin ? "Login" : "Register"}</button>
          <button type="button" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? "Switch to Register" : "Switch to Login"}
          </button>
        </form>
      ) : (
        <div>
          <h2>Welcome, {username} ({role})</h2>
          <form onSubmit={handleCreate}>
            <input
              placeholder="Policy Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
            <input
              placeholder="Details"
              value={form.details}
              onChange={(e) => setForm({ ...form, details: e.target.value })}
              required
            />
            <button type="submit">Add Policy</button>
          </form>
          <ul>
            {policies.map((p) => (
              <li key={p.id}>
                <b>{p.name}</b>: {p.details} (Owner: {p.owner})
                {role === "admin" && (
                  <button onClick={() => handleDelete(p.id)}>Delete</button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
