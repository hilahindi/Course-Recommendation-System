import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Select from 'react-select';

const INITIAL_SCHEDULE = {
  'ראשון': { active: false, start: '08:00', end: '21:00' },
  'שני': { active: false, start: '08:00', end: '21:00' },
  'שלישי': { active: false, start: '08:00', end: '21:00' },
  'רביעי': { active: false, start: '08:00', end: '21:00' },
  'חמישי': { active: false, start: '08:00', end: '21:00' },
  'שישי': { active: false, start: '08:00', end: '13:00' },
};

export default function Onboarding({ onComplete }: { onComplete: () => void }) {
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [step4Error, setStep4Error] = useState('');
  const [submitError, setSubmitError] = useState('');
  
  const [metadata, setMetadata] = useState<{tracks: any[], job_roles: any[]}>({ tracks: [], job_roles: [] });
  const [courses, setCourses] = useState<any[]>([]);
  const [yearlyCoursesMap, setYearlyCoursesMap] = useState<Record<number, number[]>>({});
  
  const [degree, setDegree] = useState('מדעי המחשב');
  const [yearOfStudy, setYearOfStudy] = useState(1);
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);
  const [selectedJobRole, setSelectedJobRole] = useState<number | null>(null);
  
  const [history, setHistory] = useState<{course_code: number, grade: number | ''}[]>([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [grade, setGrade] = useState('');
  
  const [schedule, setSchedule] = useState(INITIAL_SCHEDULE);

  useEffect(() => {
    api.getCourses()
      .then(res => setCourses(res.data))
      .catch(err => console.error("Failed to load courses:", err))
      .finally(() => setLoading(false));

    api.getMetadata()
      .then(res => {
        setMetadata(res.data);
      })
      .catch(err => console.warn("Metadata not found."));

    api.getYearlyMandatoryCourses()
      .then(res => setYearlyCoursesMap(res.data))
      .catch(err => console.error("Failed to load yearly courses:", err));
  }, []);

  // בדיקת תקינות לפי שלבים
  const isStepValid = () => {
    if (step === 1) return degree !== '';
    if (step === 2) return yearOfStudy >= 1;
    if (step === 3) return selectedJobRole !== null && selectedTrack !== null;
    if (step === 4) return history.length > 0 && !history.some(h => h.grade === '');
    if (step === 5) return calculateTotalWorkload() > 0;
    return true;
  };

  const handleAddHistory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse || !grade) return;
    const courseCode = parseInt(selectedCourse);
    if (!history.find(h => h.course_code === courseCode)) {
      setHistory([...history, { course_code: courseCode, grade: parseInt(grade) }]);
    }
    setSelectedCourse('');
    setGrade('');
    setStep4Error('');
  };

  const handleUpdateGrade = (courseCode: number, newGrade: string) => {
    const numericGrade = newGrade === '' ? '' : parseInt(newGrade);
    setHistory(history.map(h => 
      h.course_code === courseCode ? { ...h, grade: numericGrade } : h
    ));
    setStep4Error('');
    setSubmitError('');
  };

  const handleRemoveHistory = (courseCode: number) => {
    setHistory(history.filter(h => h.course_code !== courseCode));
    setStep4Error('');
    setSubmitError('');
  };

  const handleAutoFill = (year: number) => {
    const newHistory = [...history];
    const coursesForYear = yearlyCoursesMap[year] || [];
    
    coursesForYear.forEach(code => {
      if (!newHistory.find(h => h.course_code === code)) {
        newHistory.push({ course_code: code, grade: '' }); 
      }
    });
    setHistory(newHistory);
  };

  const calculateTotalWorkload = () => {
    let totalHours = 0;
    Object.values(schedule).forEach(day => {
      if (day.active && day.start && day.end) {
        const [startH, startM] = day.start.split(':').map(Number);
        const [endH, endM] = day.end.split(':').map(Number);
        let hours = endH - startH + (endM - startM) / 60;
        if (hours > 0) totalHours += hours;
      }
    });
    return Math.round(totalHours);
  };

  const handleNextFromStep4 = () => {
    if (!isStepValid()) {
      setStep4Error("יש להזין ציון לכל הקורסים ברשימה, או למחוק קורסים מיותרים.");
      return;
    }
    setStep4Error('');
    setStep(5);
  };

  const handleFinish = async () => {
    if (!user || !isStepValid()) return;
    setSubmitError('');

    setSaving(true);
    try {
      if (history.length > 0) {
        await api.addHistoryBulk(user.user_id, { courses: history });
      }
      
      const activeScheduleDays = Object.entries(schedule)
        .filter(([_, data]) => data.active)
        .map(([day, data]) => `${day} (${data.start}-${data.end})`);

      const workload = calculateTotalWorkload();
      
      await api.updateProfile(user.user_id, {
        degree,
        year_of_study: yearOfStudy,
        available_days: activeScheduleDays.join(', '), 
        target_workload: workload || 0,
        needs_flexible_attendance: false,
        interested_track_ids: selectedTrack ? [selectedTrack] : [],
        interested_job_role_ids: selectedJobRole ? [selectedJobRole] : [],
        onboarding_completed: true
      });
      
      onComplete();
    } catch (err) {
      console.error(err);
      setSubmitError("אופס! שגיאה בשמירת נתוני הפרופיל. אנא נסי שוב.");
    } finally {
      setSaving(false);
    }
  };

  const availableCourseOptions = courses.filter(c => !history.find(h => h.course_code === c.course_code));

  if (loading) return <div className="text-center mt-20 text-gray-800 text-xl" dir="rtl">טוען את המערכת...</div>;

  return (
    <div className="min-h-screen flex items-center justify-center p-4" dir="rtl">
      <div className="glass-panel w-full max-w-3xl relative overflow-hidden bg-white shadow-2xl rounded-2xl p-8">
        
        {/* Progress Bar */}
        <div className="absolute top-0 right-0 w-full h-1.5 bg-gray-100">
          <div 
            className="h-full bg-gradient-to-l from-emerald-500 to-teal-500 transition-all duration-300"
            style={{ width: `${(step / 5) * 100}%` }}
          />
        </div>

        <div className="mb-8 mt-4 text-center">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-l from-emerald-600 to-teal-600 mb-2">
            ברוכים הבאים למערכת ההמלצות
          </h1>
          <p className="text-gray-500">בואו נגדיר את הפרופיל שלכם כדי שנוכל להתאים לכם את המסלול המושלם.</p>
        </div>

        {/* STEP 1: Degree */}
        {step === 1 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">שלב 1: התואר שלך</h2>
            <div>
              <label className="block text-sm text-gray-600 mb-2 font-medium">בחר/י את מסלול הלימודים</label>
              <select 
                value={degree}
                onChange={e => setDegree(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-emerald-400"
              >
                <option value="מדעי המחשב">מדעי המחשב</option>
                <option value="הנדסת תוכנה">הנדסת תוכנה</option>
              </select>
            </div>
            <div className="flex justify-end mt-8">
              <button 
                onClick={() => setStep(2)} 
                disabled={!isStepValid()}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-2.5 rounded-lg font-medium shadow-lg transition-colors disabled:opacity-50"
              >
                המשך לשלב הבא
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Year of Study */}
        {step === 2 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">שלב 2: שנת לימודים</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(y => (
                <div 
                  key={y}
                  onClick={() => setYearOfStudy(y)}
                  className={`p-6 text-center rounded-xl cursor-pointer border-2 transition-all ${
                    yearOfStudy === y 
                    ? 'bg-emerald-50 border-emerald-500 shadow-md transform scale-105' 
                    : 'bg-white border-gray-100 hover:border-gray-300'
                  }`}
                >
                  <div className="text-3xl font-bold text-gray-800">שנה {y === 1 ? "א'" : y === 2 ? "ב'" : y === 3 ? "ג'" : "ד'"}</div>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-8">
              <button onClick={() => setStep(1)} className="text-gray-500 hover:text-gray-800 px-4 py-2">חזור</button>
              <button 
                onClick={() => setStep(3)} 
                disabled={!isStepValid()}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-2.5 rounded-lg font-medium shadow-lg transition-colors disabled:opacity-50"
              >
                המשך לשלב הבא
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Areas of Interest */}
        {step === 3 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-1 text-gray-800">שלב 3: מטרות קריירה ומסלולים</h2>
            <p className="text-sm text-gray-500 mb-6">ספר/י לנו לאן את/ה מכוון/ת בתעשייה כדי שנוכל להמליץ על הקורסים הרלוונטיים ביותר.</p>
            
            <div className="mb-8">
              <label className="block text-sm text-gray-700 mb-3 font-medium">תפקיד מבוקש בתעשייה</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {metadata.job_roles && metadata.job_roles.length > 0 ? (
                  metadata.job_roles.map((role: any) => (
                    <label
                      key={role.id}
                      className={`cursor-pointer px-4 py-3 rounded-xl border text-sm font-medium transition-all flex items-center gap-3 ${
                        selectedJobRole === role.id
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-sm'
                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <input 
                        type="radio" 
                        name="jobRole"
                        value={role.id}
                        checked={selectedJobRole === role.id}
                        onChange={() => setSelectedJobRole(role.id)}
                        className="w-4 h-4 text-emerald-500 focus:ring-emerald-500"
                      />
                      {role.title}
                    </label>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm">טוען תפקידים עדכניים מהשוק...</p>
                )}
              </div>
            </div>

            {metadata.tracks.length > 0 && (
              <div>
                <label className="block text-sm text-gray-700 mb-3 font-medium">אשכול לימודים (התמחות)</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {metadata.tracks.map((track: any) => (
                    <label
                      key={track.id}
                      className={`cursor-pointer px-4 py-3 rounded-xl border text-sm font-medium transition-all flex items-center gap-3 ${
                        selectedTrack === track.id
                        ? 'bg-teal-50 border-teal-500 text-teal-800 shadow-sm'
                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <input 
                        type="radio" 
                        name="track"
                        value={track.id}
                        checked={selectedTrack === track.id}
                        onChange={() => setSelectedTrack(track.id)}
                        className="w-4 h-4 text-teal-500 focus:ring-teal-500"
                      />
                      {track.name}
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex justify-between mt-8 pt-4">
              <button onClick={() => setStep(2)} className="text-gray-500 hover:text-gray-800 px-4 py-2">חזור</button>
              <button 
                onClick={() => setStep(4)} 
                disabled={!isStepValid()}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-2.5 rounded-lg font-medium shadow-lg transition-colors disabled:opacity-50"
              >
                המשך לשלב הבא
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: Course History */}
        {step === 4 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-1 text-gray-800">שלב 4: היסטוריית קורסים</h2>
            <p className="text-sm text-gray-500 mb-4">הזן/י את הקורסים שכבר עברת כדי שלא נמליץ עליהם שוב.</p>

            {yearOfStudy > 1 && (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
                <h4 className="font-medium text-blue-800 mb-2">מילוי אוטומטי חכם ⚡</h4>
                <p className="text-xs text-blue-600 mb-3">חסוך זמן! הוסף בלחיצה את כל קורסי החובה של השנים הקודמות.</p>
                <div className="flex gap-2 flex-wrap">
                  {[...Array(yearOfStudy - 1)].map((_, i) => (
                    <button 
                      key={i}
                      onClick={() => handleAutoFill(i + 1)}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg transition-colors shadow-sm"
                    >
                      השלם קורסי חובה לשנה {i + 1 === 1 ? "א'" : i + 1 === 2 ? "ב'" : "ג'"}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <form onSubmit={handleAddHistory} className="bg-gray-50 p-4 rounded-xl border border-gray-200 flex flex-row items-end gap-3 w-full">
              <div className="flex flex-col flex-[3] text-right">
                <label className="text-xs text-gray-600 mb-1.5 mr-1 font-medium">חפש או בחר קורס</label>
                <Select
                  className="text-sm"
                  placeholder="הקלד שם או מספר קורס..."
                  options={availableCourseOptions.map(c => ({
                    value: c.course_code,
                    label: `${c.course_code} - ${c.name}`
                  }))}
                  onChange={(selected: any) => setSelectedCourse(selected ? selected.value : '')}
                  isSearchable
                  isClearable
                  noOptionsMessage={() => "לא נמצאו קורסים"}
                  styles={{
                    control: (base) => ({
                      ...base,
                      borderRadius: '0.5rem',
                      borderColor: '#D1D5DB',
                      height: '40px',
                      minHeight: '40px',
                      maxHeight: '40px',
                      boxShadow: 'none',
                      '&:hover': { borderColor: '#34D399' }
                    }),
                  }}
                />
              </div>

              <div className="flex flex-col w-24 text-right">
                <label className="text-xs text-gray-600 mb-1.5 mr-1 font-medium">ציון</label>
                <input 
                  type="number" 
                  min="0" max="100" 
                  placeholder="0-100"
                  value={grade}
                  onChange={e => setGrade(e.target.value)}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 h-10 text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 m-0 box-border"
                />
              </div>

              <button 
                type="submit" 
                disabled={!selectedCourse || !grade}
                className="bg-emerald-100 text-emerald-800 hover:bg-emerald-200 font-medium px-6 h-10 rounded-lg disabled:opacity-50 transition-colors whitespace-nowrap flex items-center justify-center shrink-0 m-0" 
              >
                הוסף
              </button>
            </form>

            {history.length > 0 && (
              <div className="mt-6 border border-gray-100 rounded-xl overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 flex justify-between items-center text-sm font-semibold text-gray-600 border-b border-gray-100">
                  <span>קורס</span>
                  <span className="ml-20">ציון</span>
                </div>
                <div className="max-h-60 overflow-y-auto custom-scrollbar divide-y divide-gray-100" dir="ltr">
                  {history.map((h, i) => {
                    const course = courses.find(c => c.course_code === h.course_code);
                    return (
                      <div key={i} dir="rtl" className="flex justify-between items-center bg-white p-3 px-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-center gap-3 text-right">
                          <span>
                            <span className="text-emerald-700 font-mono font-medium ml-2">{h.course_code}</span> 
                            {course?.name || 'קורס לא ידוע'}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-20">
                            <input 
                              type="number"
                              min="0" max="100"
                              placeholder="הזן ציון"
                              value={h.grade}
                              onChange={(e) => handleUpdateGrade(h.course_code, e.target.value)}
                              className={`w-full text-center border rounded p-1 text-sm font-semibold focus:outline-none focus:border-emerald-400 focus:bg-white transition-colors mt-4 ${
                                h.grade === '' ? 'border-red-300 bg-red-50 text-red-700' : 'border-gray-200 bg-gray-50 text-gray-700'
                              }`}
                            />
                          </div>
                          <button 
                            onClick={() => handleRemoveHistory(h.course_code)}
                            type="button"
                            className="text-red-500 bg-transparent hover:bg-red-50 hover:text-red-700 p-2 rounded-md transition-colors border-none"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex justify-between items-center mt-8 pt-4 border-t border-gray-100 pb-6">
              <button onClick={() => setStep(3)} className="text-gray-500 hover:text-gray-800 px-4 py-2">חזור</button>
              <div className="relative">
                <button 
                  onClick={handleNextFromStep4} 
                  disabled={!isStepValid()}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-2.5 rounded-lg font-medium shadow-lg transition-colors disabled:opacity-50"
                >
                  המשך לשלב הבא
                </button>
                {step4Error && (
                  <span className="absolute top-full right-0 mt-2 text-red-500 text-sm font-medium w-max">
                    {step4Error}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* STEP 5: Availability */}
        {step === 5 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-xl font-semibold mb-1 text-gray-800">שלב 5: זמני למידה (מערכת שעות)</h2>
            <p className="text-sm text-gray-500 mb-6">סמן/י באילו ימים ושעות את/ה פנוי/ה להגיע להרצאות או ללמוד בבית.</p>
            
            <div className="space-y-3">
              {Object.entries(schedule).map(([dayName, data]) => (
                <div key={dayName} className={`flex items-center gap-4 p-3 rounded-xl border transition-colors ${data.active ? 'bg-emerald-50 border-emerald-200' : 'bg-gray-50 border-gray-200'}`}>
                  <label className="flex items-center gap-3 cursor-pointer w-28">
                    <input 
                      type="checkbox"
                      checked={data.active}
                      onChange={(e) => setSchedule({
                        ...schedule,
                        [dayName]: { ...data, active: e.target.checked }
                      })}
                      className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                    />
                    <span className={`font-medium ${data.active ? 'text-emerald-800' : 'text-gray-500'}`}>יום {dayName}</span>
                  </label>
                  <div className={`flex items-center gap-2 flex-grow transition-opacity duration-200 ${data.active ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
                    <span className="text-sm text-gray-500">מ-</span>
                    <input 
                      type="time" 
                      value={data.start}
                      onChange={(e) => setSchedule({...schedule, [dayName]: { ...data, start: e.target.value }})}
                      className="bg-white border border-gray-300 rounded-md p-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                    />
                    <span className="text-sm text-gray-500">עד-</span>
                    <input 
                      type="time" 
                      value={data.end}
                      onChange={(e) => setSchedule({...schedule, [dayName]: { ...data, end: e.target.value }})}
                      className="bg-white border border-gray-300 rounded-md p-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-gray-100 p-4 rounded-xl mt-6 flex justify-between items-center border border-gray-200">
              <span className="text-gray-600 font-medium">סך שעות למידה פנויות בשבוע:</span>
              <span className="text-2xl font-bold text-gray-800">{calculateTotalWorkload()} <span className="text-sm font-normal">שעות</span></span>
            </div>

            <div className="flex justify-between items-center mt-8 pt-4 border-t border-gray-200 pb-6">
              <button onClick={() => setStep(4)} className="text-gray-500 hover:text-gray-800 px-4 py-2">חזור</button>
              <div className="relative">
                <button 
                  onClick={handleFinish} 
                  disabled={saving || !isStepValid()}
                  className="bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white px-8 py-3 rounded-xl font-bold shadow-lg shadow-emerald-500/30 disabled:opacity-50 transition-all transform hover:scale-105"
                >
                  {saving ? 'מגדיר פרופיל...' : 'סיים ומעבר לדשבורד'}
                </button>
                {submitError && (
                  <span className="absolute top-full right-0 mt-2 text-red-500 text-sm font-medium w-max">
                    {submitError}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}