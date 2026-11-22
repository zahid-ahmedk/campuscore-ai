"use client";

import React, { useState, useEffect } from "react";
import {
  GraduationCap,
  Users,
  AlertTriangle,
  Sparkles,
  CreditCard,
  BookOpen,
  Building2,
  UserPlus,
  Send,
  LogOut,
  CheckCircle2,
  Clock,
  XCircle,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000/api";

type UserSession = {
  id: number;
  full_name: string;
  email: string;
  role: "admin" | "chairman" | "clerk" | "student";
  department_id: number | null;
};

export default function CampusCoreApp() {
  const [user, setUser] = useState<UserSession | null>(null);
  const [email, setEmail] = useState("admin@campuscore.edu");
  const [password, setPassword] = useState("admin123");
  const [loginError, setLoginError] = useState("");

  const [departments, setDepartments] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [batchFilter, setBatchFilter] = useState("21");

  const [deptName, setDeptName] = useState("");
  const [deptCode, setDeptCode] = useState("");
  const [staffName, setStaffName] = useState("");
  const [staffEmail, setStaffEmail] = useState("");
  const [staffPassword, setStaffPassword] = useState("pass123");
  const [staffDeptId, setStaffDeptId] = useState(1);

  const [stuRoll, setStuRoll] = useState("");
  const [stuName, setStuName] = useState("");
  const [stuEmail, setStuEmail] = useState("");
  const [stuBatch, setStuBatch] = useState("21");
  const [stuAttendance, setStuAttendance] = useState("85");
  const [stuCgpa, setStuCgpa] = useState("3.2");
  const [stuPaid, setStuPaid] = useState("45000");

  const [copilotQ, setCopilotQ] = useState("");
  const [copilotRes, setCopilotRes] = useState<any>(null);
  const [studentProfile, setStudentProfile] = useState<any>(null);
  const [toast, setToast] = useState("");

  const notify = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3500);
  };

  const fetchAllData = async () => {
    try {
      const [deptRes, stuRes] = await Promise.all([
        fetch(`${API_BASE}/departments`),
        fetch(`${API_BASE}/students`),
      ]);
      if (deptRes.ok) setDepartments(await deptRes.json());
      if (stuRes.ok) setStudents(await stuRes.json());
    } catch {
      notify("Backend offline — make sure uvicorn is running on port 8000");
    }
  };

  const fetchStudentProfile = async (rollNo: string) => {
    const res = await fetch(`${API_BASE}/students/${rollNo}/profile`);
    if (res.ok) setStudentProfile(await res.json());
  };

  useEffect(() => {
    if (user) {
      fetchAllData();
      if (user.role === "student") {
        fetchStudentProfile("21IT-95");
      }
    }
  }, [user]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    try {
      const res = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        setLoginError("Invalid email or password");
        return;
      }
      const data = await res.json();
      setUser(data);
    } catch {
      setLoginError("Cannot connect to backend server (http://127.0.0.1:8000)");
    }
  };

  const quickFill = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
  };

  const handleAddDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch(`${API_BASE}/departments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: deptName, code: deptCode }),
    });
    if (res.ok) {
      setDeptName("");
      setDeptCode("");
      notify("Department created!");
      fetchAllData();
    } else {
      notify("Error: Department code already exists");
    }
  };

  const handleAddStaff = async (e: React.FormEvent, role: "chairman" | "clerk") => {
    e.preventDefault();
    const res = await fetch(`${API_BASE}/staff`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: staffName,
        email: staffEmail,
        password: staffPassword,
        role,
        department_id: Number(staffDeptId),
      }),
    });
    if (res.ok) {
      setStaffName("");
      setStaffEmail("");
      notify(`${role.toUpperCase()} account created!`);
    }
  };

  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch(`${API_BASE}/students`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        roll_no: stuRoll,
        full_name: stuName,
        email: stuEmail,
        batch: stuBatch,
        department_id: 1,
        attendance_percentage: Number(stuAttendance),
        cgpa: Number(stuCgpa),
        total_fee: 45000,
        paid_amount: Number(stuPaid),
      }),
    });
    if (res.ok) {
      const data = await res.json();
      setStuRoll("");
      setStuName("");
      setStuEmail("");
      notify(`Student added! ML Risk Level: ${data.ai_risk.risk_level}`);
      fetchAllData();
    } else {
      notify("Roll number already exists");
    }
  };

  const handleMarkPaid = async (feeId: number) => {
    const res = await fetch(`${API_BASE}/fees/${feeId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paid_amount: 45000 }),
    });
    if (res.ok) {
      notify("Fee cleared & receipt updated!");
      fetchAllData();
    }
  };

  const handleAskCopilot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!copilotQ.trim()) return;
    const res = await fetch(`${API_BASE}/ai/copilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: copilotQ }),
    });
    if (res.ok) setCopilotRes(await res.json());
  };

  const UniversityLogo = () => (
    <div className="flex items-center gap-3">
      <div className="w-11 h-11 rounded-xl flex items-center justify-center font-bold text-white shadow-md bg-sky-600">
        <GraduationCap className="w-6 h-6" />
      </div>
      <div>
        <h1 className="font-bold text-slate-900 leading-tight">
          CampusCore <span className="text-sky-600">AI</span>
        </h1>
        <p className="text-xs text-slate-500">
          QUEST Nawabshah • Department of IT
        </p>
      </div>
    </div>
  );

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-sky-950 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 space-y-6">
          <UniversityLogo />

          <div className="border-t pt-4">
            <h2 className="text-xl font-bold text-slate-800">Sign in to CampusCore</h2>
            <p className="text-sm text-slate-500">
              AI-Powered Academic, Fee & Predictive Risk Management
            </p>
          </div>

          <div className="grid grid-cols-4 gap-2">
            {[
              { label: "Admin", e: "admin@campuscore.edu", p: "admin123" },
              { label: "Chairman", e: "chairman@campuscore.edu", p: "chair123" },
              { label: "Clerk", e: "clerk@campuscore.edu", p: "clerk123" },
              { label: "Student", e: "21it95@student.campuscore.edu", p: "student123" },
            ].map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => quickFill(item.e, item.p)}
                className={`py-1.5 px-2 text-xs font-semibold rounded-lg border transition ${
                  email === item.e
                    ? "bg-sky-600 text-white border-sky-600"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Institutional Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-slate-900 text-sm focus:ring-2 focus:ring-sky-500 outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-slate-900 text-sm focus:ring-2 focus:ring-sky-500 outline-none"
                required
              />
            </div>
            {loginError && <p className="text-xs text-red-600 font-medium">{loginError}</p>}
            <button
              type="submit"
              className="w-full py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg shadow transition"
            >
              Sign In to Dashboard
            </button>
          </form>
        </div>
      </div>
    );
  }

  const filteredStudents = batchFilter
    ? students.filter((s) => s.batch === batchFilter)
    : students;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-10">
        <UniversityLogo />

        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-semibold text-slate-800">{user.full_name}</p>
            <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-sky-50 text-sky-700">
              {user.role}
            </span>
          </div>

          <button
            onClick={() => setUser(null)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 text-xs font-semibold"
          >
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </header>

      {toast && (
        <div className="fixed bottom-5 right-5 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-lg text-sm flex items-center gap-2 z-50">
          <Sparkles className="w-4 h-4 text-amber-400" /> {toast}
        </div>
      )}

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {user.role === "admin" && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase">Total Departments</p>
                <p className="text-2xl font-bold mt-1">{departments.length}</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase">Enrolled Students</p>
                <p className="text-2xl font-bold mt-1">{students.length}</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase">AI High-Risk Alerts</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {students.filter((s) => s.risk_level === "High").length}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="font-bold text-lg flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-sky-600" /> Manage Departments
                </h3>
                <form onSubmit={handleAddDepartment} className="flex gap-2">
                  <input
                    placeholder="Department Name (e.g. Software Eng)"
                    value={deptName}
                    onChange={(e) => setDeptName(e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-lg text-sm"
                    required
                  />
                  <input
                    placeholder="Code (SE1)"
                    value={deptCode}
                    onChange={(e) => setDeptCode(e.target.value)}
                    className="w-28 px-3 py-2 border rounded-lg text-sm"
                    required
                  />
                  <button className="px-4 py-2 bg-sky-600 text-white rounded-lg text-sm font-semibold">
                    Add
                  </button>
                </form>

                <div className="divide-y">
                  {departments.map((d) => (
                    <div key={d.id} className="py-2.5 flex justify-between text-sm">
                      <span className="font-medium">{d.name}</span>
                      <span className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono">
                        {d.code}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="font-bold text-lg flex items-center gap-2">
                  <UserPlus className="w-5 h-5 text-sky-600" /> Assign Department Chairman
                </h3>
                <form onSubmit={(e) => handleAddStaff(e, "chairman")} className="space-y-3">
                  <input
                    placeholder="Chairman Full Name"
                    value={staffName}
                    onChange={(e) => setStaffName(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                    required
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="email"
                      placeholder="Email"
                      value={staffEmail}
                      onChange={(e) => setStaffEmail(e.target.value)}
                      className="px-3 py-2 border rounded-lg text-sm"
                      required
                    />
                    <select
                      value={staffDeptId}
                      onChange={(e) => setStaffDeptId(Number(e.target.value))}
                      className="px-3 py-2 border rounded-lg text-sm"
                    >
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button className="w-full py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold">
                    Create Chairman Account
                  </button>
                </form>
              </div>
            </div>

            <div className="bg-gradient-to-r from-sky-50 to-indigo-50 p-6 rounded-xl border border-sky-200 space-y-4">
              <h3 className="font-bold text-lg flex items-center gap-2 text-slate-900">
                <Sparkles className="w-5 h-5 text-sky-600" /> AI Campus Analytics Copilot
              </h3>
              <form onSubmit={handleAskCopilot} className="flex gap-2">
                <input
                  placeholder='Ask e.g. "Which students are at high risk?" or "Show pending fee summary"'
                  value={copilotQ}
                  onChange={(e) => setCopilotQ(e.target.value)}
                  className="flex-1 px-4 py-2.5 bg-white border border-sky-200 rounded-lg text-sm"
                />
                <button className="px-5 py-2.5 bg-sky-600 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5">
                  <Send className="w-4 h-4" /> Ask AI
                </button>
              </form>
              {copilotRes && (
                <div className="bg-white p-4 rounded-lg border border-sky-100 text-sm text-slate-800">
                  <p className="font-semibold text-sky-700 mb-1">AI Insight:</p>
                  <p>{copilotRes.answer}</p>
                </div>
              )}
            </div>
          </>
        )}

        {user.role === "chairman" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-sky-600" /> Add Department Clerk
              </h3>
              <form
                onSubmit={(e) => handleAddStaff(e, "clerk")}
                className="grid grid-cols-1 md:grid-cols-4 gap-3"
              >
                <input
                  placeholder="Clerk Name"
                  value={staffName}
                  onChange={(e) => setStaffName(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  type="email"
                  placeholder="Clerk Email"
                  value={staffEmail}
                  onChange={(e) => setStaffEmail(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={staffPassword}
                  onChange={(e) => setStaffPassword(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <button className="bg-sky-600 text-white rounded-lg text-sm font-semibold py-2">
                  + Add Clerk
                </button>
              </form>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" /> Departmental Academic & ML
                  Dropout Risk Monitor
                </h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
                    <tr>
                      <th className="p-3">Roll No</th>
                      <th className="p-3">Student Name</th>
                      <th className="p-3">Attendance</th>
                      <th className="p-3">CGPA</th>
                      <th className="p-3">Fee Status</th>
                      <th className="p-3">AI Risk Prediction</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {students.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50">
                        <td className="p-3 font-mono font-semibold">{s.roll_no}</td>
                        <td className="p-3">{s.full_name}</td>
                        <td className="p-3">{s.attendance_percentage}%</td>
                        <td className="p-3 font-semibold">{s.cgpa.toFixed(2)}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              s.fee.status === "Paid"
                                ? "bg-emerald-100 text-emerald-700"
                                : s.fee.status === "Partial"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {s.fee.status}
                          </span>
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                              s.risk_level === "High"
                                ? "bg-red-100 text-red-700"
                                : s.risk_level === "Medium"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-emerald-100 text-emerald-700"
                            }`}
                          >
                            {s.risk_level} ({Math.round(s.risk_score * 100)}%)
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {user.role === "clerk" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <Users className="w-5 h-5 text-sky-600" /> Register New Student
              </h3>
              <form
                onSubmit={handleAddStudent}
                className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3"
              >
                <input
                  placeholder="Roll No (e.g. 21IT-105)"
                  value={stuRoll}
                  onChange={(e) => setStuRoll(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  placeholder="Full Name"
                  value={stuName}
                  onChange={(e) => setStuName(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  type="email"
                  placeholder="Student Email"
                  value={stuEmail}
                  onChange={(e) => setStuEmail(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  placeholder="Batch (e.g. 21)"
                  value={stuBatch}
                  onChange={(e) => setStuBatch(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  type="number"
                  placeholder="Attendance %"
                  value={stuAttendance}
                  onChange={(e) => setStuAttendance(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="CGPA"
                  value={stuCgpa}
                  onChange={(e) => setStuCgpa(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <input
                  type="number"
                  placeholder="Paid Fee (out of 45000)"
                  value={stuPaid}
                  onChange={(e) => setStuPaid(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  required
                />
                <button className="bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold py-2">
                  + Add Student
                </button>
              </form>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-bold text-lg flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-sky-600" /> View & Reconcile Fees by Batch
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Filter Batch:</span>
                  <input
                    value={batchFilter}
                    onChange={(e) => setBatchFilter(e.target.value)}
                    placeholder="e.g. 21"
                    className="w-24 px-3 py-1.5 border rounded-lg text-sm font-mono"
                  />
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
                    <tr>
                      <th className="p-3">Roll No</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Batch</th>
                      <th className="p-3">Total Fee</th>
                      <th className="p-3">Paid</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredStudents.map((s) => (
                      <tr key={s.id}>
                        <td className="p-3 font-mono font-semibold">{s.roll_no}</td>
                        <td className="p-3">{s.full_name}</td>
                        <td className="p-3">{s.batch}</td>
                        <td className="p-3">PKR {s.fee.total_fee.toLocaleString()}</td>
                        <td className="p-3">PKR {s.fee.paid_amount.toLocaleString()}</td>
                        <td className="p-3">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                              s.fee.status === "Paid"
                                ? "bg-emerald-100 text-emerald-700"
                                : s.fee.status === "Partial"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {s.fee.status === "Paid" && <CheckCircle2 className="w-3.5 h-3.5" />}
                            {s.fee.status === "Partial" && <Clock className="w-3.5 h-3.5" />}
                            {s.fee.status === "Pending" && <XCircle className="w-3.5 h-3.5" />}
                            {s.fee.status}
                          </span>
                        </td>
                        <td className="p-3">
                          {s.fee.status !== "Paid" ? (
                            <button
                              onClick={() => handleMarkPaid(s.fee.id)}
                              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg"
                            >
                              Mark Full Paid
                            </button>
                          ) : (
                            <span className="text-xs text-slate-400">Cleared</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {user.role === "student" && studentProfile && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-5 rounded-xl border border-slate-200">
              <div>
                <h2 className="text-xl font-bold">{studentProfile.student.full_name}</h2>
                <p className="text-sm text-slate-500">
                  Roll No: {studentProfile.student.roll_no} • Batch {studentProfile.student.batch} •{" "}
                  {studentProfile.student.department}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Preview Student Record:</span>
                {["21IT-95", "21IT-98", "21IT-70"].map((r) => (
                  <button
                    key={r}
                    onClick={() => fetchStudentProfile(r)}
                    className="px-2.5 py-1 text-xs font-mono border rounded hover:bg-slate-100"
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200">
                <p className="text-xs text-slate-500 uppercase font-semibold">Cumulative GPA</p>
                <p className="text-3xl font-bold text-sky-600 mt-1">
                  {studentProfile.student.cgpa.toFixed(2)} / 4.00
                </p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200">
                <p className="text-xs text-slate-500 uppercase font-semibold">Attendance Rate</p>
                <p className="text-3xl font-bold mt-1">
                  {studentProfile.student.attendance_percentage}%
                </p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200">
                <p className="text-xs text-slate-500 uppercase font-semibold">
                  ML Academic Risk Status
                </p>
                <p
                  className={`text-2xl font-bold mt-1 ${
                    studentProfile.ai_risk_analysis.risk_level === "High"
                      ? "text-red-600"
                      : "text-emerald-600"
                  }`}
                >
                  {studentProfile.ai_risk_analysis.risk_level} Risk
                </p>
              </div>
            </div>

            <div className="bg-gradient-to-r from-sky-600 to-indigo-700 text-white p-6 rounded-xl shadow-md space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-300" />
                <h3 className="font-bold text-lg">{studentProfile.ai_study_plan.summary}</h3>
              </div>
              <ul className="space-y-2 text-sm text-sky-50 list-disc pl-5">
                {studentProfile.ai_study_plan.action_steps.map((step: string, idx: number) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200">
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-sky-600" /> Semester Course Score Sheet
              </h3>
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-xs uppercase text-slate-600">
                  <tr>
                    <th className="p-3">Code</th>
                    <th className="p-3">Course Title</th>
                    <th className="p-3">Midterm (30)</th>
                    <th className="p-3">Sessional (20)</th>
                    <th className="p-3">Final (50)</th>
                    <th className="p-3">Total</th>
                    <th className="p-3">Grade</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {studentProfile.grades.map((g: any, idx: number) => (
                    <tr key={idx}>
                      <td className="p-3 font-mono font-semibold">{g.course_code}</td>
                      <td className="p-3">{g.course_name}</td>
                      <td className="p-3">{g.midterm_marks}</td>
                      <td className="p-3">{g.sessional_marks}</td>
                      <td className="p-3">{g.final_marks}</td>
                      <td className="p-3 font-bold">{g.total} / 100</td>
                      <td className="p-3 font-bold text-sky-600">{g.grade_letter}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
