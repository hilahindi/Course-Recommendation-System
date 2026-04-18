import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

const YEAR_1_COURSES = [1001, 1002, 1003, 1004, 1005];

export default function Onboarding({ onComplete }: { onComplete: () => void }) {
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [metadata, setMetadata] = useState({ tracks: [], job_roles: [] });
  const [courses, setCourses] = useState<any[]>([]);
  
  // Form State
  const [degree, setDegree] = useState('Computer Science');
  const [yearOfStudy, setYearOfStudy] = useState(1);
  const [interestedTracks, setInterestedTracks] = useState<number[]>([]);
  const [interestedJobRoles, setInterestedJobRoles] = useState<number[]>([]);
  
  // History State
  const [history, setHistory] = useState<{course_code: number, grade: number}[]>([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [grade, setGrade] = useState('');
  
  // Availability State
  const [availableDays, setAvailableDays] = useState<string[]>([]);
  const [hoursPerDay, setHoursPerDay] = useState(3);

  const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  useEffect(() => {
    Promise.all([
      api.getMetadata(),
      api.getCourses()
    ]).then(([metaRes, courseRes]) => {
      setMetadata(metaRes.data);
      setCourses(courseRes.data);
    }).catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleAddHistory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse || !grade) return;
    const courseCode = parseInt(selectedCourse);
    if (!history.find(h => h.course_code === courseCode)) {
      setHistory([...history, { course_code: courseCode, grade: parseInt(grade) }]);
    }
    setSelectedCourse('');
    setGrade('');
  };

  const handleAutoFill = () => {
    const newHistory = [...history];
    YEAR_1_COURSES.forEach(code => {
      if (!newHistory.find(h => h.course_code === code)) {
        newHistory.push({ course_code: code, grade: 85 }); // Default passing grade
      }
    });
    setHistory(newHistory);
  };

  const handleFinish = async () => {
    if (!user) return;
    setSaving(true);
    try {
      // 1. Submit bulk history
      if (history.length > 0) {
        await api.addHistoryBulk(user.user_id, { courses: history });
      }
      
      // 2. Submit profile
      const workload = availableDays.length * hoursPerDay;
      await api.updateProfile(user.user_id, {
        degree,
        year_of_study: yearOfStudy,
        available_days: availableDays.join(','),
        target_workload: workload || 3,
        needs_flexible_attendance: false,
        interested_track_ids: interestedTracks,
        interested_job_role_ids: interestedJobRoles,
        onboarding_completed: true
      });
      
      onComplete();
    } catch (err) {
      console.error(err);
      alert("Failed to save onboarding data.");
    } finally {
      setSaving(false);
    }
  };

  const availableCourseOptions = courses.filter(c => !history.find(h => h.course_code === c.course_code));

  if (loading) return <div className="text-center mt-20 text-white text-xl">Loading wizard...</div>;

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-2xl relative overflow-hidden">
        {/* Progress Bar */}
        <div className="absolute top-0 left-0 w-full h-1.5 bg-white/10">
          <div 
            className="h-full bg-gradient-to-r from-blue-400 to-purple-500 transition-all duration-300"
            style={{ width: `${(step / 5) * 100}%` }}
          />
        </div>

        <div className="mb-8 mt-4 text-center">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
            Welcome to Afeka Recommender
          </h1>
          <p className="text-white/60">Let's set up your profile to get the best course recommendations.</p>
        </div>

        {/* STEP 1: Degree */}
        {step === 1 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-4">Step 1: Your Degree</h2>
            <div>
              <label className="block text-sm text-white/70 mb-2">Select your degree program</label>
              <select 
                value={degree}
                onChange={e => setDegree(e.target.value)}
                className="w-full bg-black/30 border border-white/20 rounded-lg p-3 text-white focus:outline-none focus:border-blue-400"
              >
                <option value="Computer Science">Computer Science</option>
              </select>
              <p className="text-xs text-white/40 mt-2">* Currently, only Computer Science is supported.</p>
            </div>
            <div className="flex justify-end mt-8">
              <button onClick={() => setStep(2)} className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg font-medium shadow-lg shadow-blue-500/20">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 2: Year of Study */}
        {step === 2 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-4">Step 2: Year of Study</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(y => (
                <div 
                  key={y}
                  onClick={() => setYearOfStudy(y)}
                  className={`p-4 text-center rounded-xl cursor-pointer border transition-all ${
                    yearOfStudy === y 
                    ? 'bg-blue-600/40 border-blue-400 shadow-lg shadow-blue-500/20' 
                    : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <div className="text-2xl font-bold">{y}</div>
                  <div className="text-xs text-white/60">{y === 1 ? 'st' : y === 2 ? 'nd' : y === 3 ? 'rd' : 'th'} Year</div>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-8">
              <button onClick={() => setStep(1)} className="text-white/60 hover:text-white">Back</button>
              <button onClick={() => setStep(3)} className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg font-medium shadow-lg shadow-blue-500/20">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 3: Areas of Interest */}
        {step === 3 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-1">Step 3: Career Goals & Tracks</h2>
            <p className="text-sm text-white/50 mb-6">Tell us about your career aspirations to get tailored recommendations.</p>
            
            <div className="mb-6">
              <label className="block text-sm text-white/80 mb-3">Industry Role (Select 1 or more)</label>
              <div className="flex flex-wrap gap-3">
                {metadata.job_roles.map((role: any) => (
                  <button
                    key={role.id}
                    onClick={() => setInterestedJobRoles(prev => prev.includes(role.id) ? prev.filter(id => id !== role.id) : [...prev, role.id])}
                    className={`px-4 py-2 rounded-xl border text-sm font-medium transition-all ${
                      interestedJobRoles.includes(role.id)
                      ? 'bg-blue-600 text-white border-blue-400 shadow-lg shadow-blue-500/30'
                      : 'bg-white/5 text-white/70 border-white/10 hover:bg-white/10 hover:text-white'
                    }`}
                  >
                    {role.title}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-white/80 mb-3">Academic Clusters</label>
              <div className="flex flex-wrap gap-3">
                {metadata.tracks.map((track: any) => (
                  <button
                    key={track.id}
                    onClick={() => setInterestedTracks(prev => prev.includes(track.id) ? prev.filter(id => id !== track.id) : [...prev, track.id])}
                    className={`px-4 py-2 rounded-full border text-sm transition-all ${
                      interestedTracks.includes(track.id)
                      ? 'bg-purple-600 text-white border-purple-400 shadow-lg shadow-purple-500/30'
                      : 'bg-white/5 text-white/70 border-white/10 hover:bg-white/10 hover:text-white'
                    }`}
                  >
                    {track.name}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-between mt-8 pt-4">
              <button onClick={() => setStep(2)} className="text-white/60 hover:text-white">Back</button>
              <button onClick={() => setStep(4)} className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg font-medium shadow-lg shadow-blue-500/20">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 4: Course History */}
        {step === 4 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-1">Step 4: Course History</h2>
            <p className="text-sm text-white/50 mb-4">Add the courses you've already passed so we don't recommend them again.</p>

            {yearOfStudy > 1 && (
              <div className="bg-blue-900/30 border border-blue-400/30 rounded-xl p-4 mb-6 flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-blue-300">Smart Auto-fill</h4>
                  <p className="text-xs text-white/60">Instantly log all standard Year 1 mandatory courses.</p>
                </div>
                <button 
                  onClick={handleAutoFill}
                  className="bg-blue-600/80 hover:bg-blue-500 text-sm px-4 py-2 rounded-lg transition-colors"
                >
                  Auto-fill Year 1
                </button>
              </div>
            )}

            <form onSubmit={handleAddHistory} className="flex gap-3 items-end bg-black/20 p-3 rounded-xl border border-white/10">
              <div className="flex-grow">
                <label className="block text-xs text-white/60 mb-1 pl-1">Select Course</label>
                <select 
                  value={selectedCourse}
                  onChange={e => setSelectedCourse(e.target.value)}
                  className="w-full bg-white/5 border border-white/20 rounded-lg p-2.5 text-white text-sm focus:outline-none focus:border-blue-400"
                >
                  <option value="">-- Choose Course --</option>
                  {availableCourseOptions.map(c => (
                    <option key={c.course_code} value={c.course_code}>
                      {c.course_code} - {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="w-24">
                <label className="block text-xs text-white/60 mb-1 pl-1">Grade</label>
                <input 
                  type="number" min="0" max="100" placeholder="0-100"
                  value={grade}
                  onChange={e => setGrade(e.target.value)}
                  className="w-full bg-white/5 border border-white/20 rounded-lg p-2.5 text-white text-sm focus:outline-none focus:border-blue-400"
                />
              </div>
              <button 
                type="submit" 
                disabled={!selectedCourse || !grade}
                className="bg-white/10 hover:bg-white/20 border border-white/20 p-2.5 rounded-lg disabled:opacity-50"
              >
                Add
              </button>
            </form>

            {history.length > 0 && (
              <div className="max-h-40 overflow-y-auto pr-2 custom-scrollbar space-y-2 mt-4">
                {history.map((h, i) => {
                  const course = courses.find(c => c.course_code === h.course_code);
                  return (
                    <div key={i} className="flex justify-between items-center bg-white/5 p-2 px-4 rounded border border-white/5 text-sm">
                      <span><span className="text-blue-300 font-mono mr-2">{h.course_code}</span> {course?.name}</span>
                      <span className="font-bold text-white/80">{h.grade}</span>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex justify-between mt-8 pt-4">
              <button onClick={() => setStep(3)} className="text-white/60 hover:text-white">Back</button>
              <button onClick={() => setStep(5)} className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg font-medium shadow-lg shadow-blue-500/20">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 5: Availability */}
        {step === 5 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-1">Step 5: Study Availability</h2>
            <p className="text-sm text-white/50 mb-4">When do you have time to attend classes and study?</p>
            
            <div className="mb-6">
              <label className="block text-sm text-white/80 mb-3">Which days are you available?</label>
              <div className="flex flex-wrap gap-2">
                {DAYS.map(day => (
                  <button
                    key={day}
                    onClick={() => setAvailableDays(prev => prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day])}
                    className={`w-14 h-14 rounded-xl border flex items-center justify-center transition-all font-medium ${
                      availableDays.includes(day)
                      ? 'bg-blue-600 border-blue-400 text-white shadow-lg shadow-blue-500/30'
                      : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10 hover:text-white/80'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-white/80 mb-2">Hours per available day</label>
              <input 
                type="number" min="1" max="12"
                value={hoursPerDay}
                onChange={e => setHoursPerDay(parseInt(e.target.value) || 0)}
                className="w-1/2 bg-black/30 border border-white/20 rounded-lg p-3 text-white focus:outline-none focus:border-blue-400 text-xl"
              />
              <p className="text-xs text-white/40 mt-2">
                Total estimated capacity: <span className="text-white font-bold">{availableDays.length * hoursPerDay} hours/week</span>
              </p>
            </div>

            <div className="flex justify-between mt-8 pt-4 border-t border-white/10">
              <button onClick={() => setStep(4)} className="text-white/60 hover:text-white">Back</button>
              <button 
                onClick={handleFinish} 
                disabled={saving || availableDays.length === 0}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 px-8 py-2 rounded-lg font-medium shadow-lg shadow-purple-500/30 disabled:opacity-50"
              >
                {saving ? 'Completing Setup...' : 'Finish & View Dashboard'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
