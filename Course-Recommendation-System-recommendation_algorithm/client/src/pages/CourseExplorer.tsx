import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import ReviewModal from '../components/ReviewModal';

function CourseModal({ course, courses, onClose, onOpenReviews }: { course: any, courses: any[], onClose: () => void, onOpenReviews: () => void }) {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCourseReviews(course.course_code)
      .then(res => setReviews(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [course]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-100 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto relative !p-8 shadow-[0_0_50px_rgba(37,99,235,0.2)]">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-800 bg-gray-100 hover:bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center transition-all"
        >
          ✕
        </button>
        
        <div className="mb-6 border-b border-gray-200 pb-6">
          <div className="flex items-center gap-3 mb-2">
            <span className="bg-blue-500/20 px-3 py-1 rounded text-sm text-emerald-700 font-mono border border-blue-500/30">
              {course.course_code}
            </span>
            <h2 className="text-3xl font-bold">{course.name}</h2>
          </div>
          <p className="text-gray-500">תקציר הסילבוס ופרטי הקורס יופיעו כאן. קורס זה דורש {course.workload} שעות השקעה שבועיות והנוכחות בו {course.mandatory_attendance ? 'חובה בהחלט' : 'גמישה'}.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div>
            <h3 className="text-lg font-semibold text-emerald-700 mb-3 border-b border-blue-500/20 pb-2">כישורים נרכשים</h3>
            {course.skills?.length > 0 ? (
              <ul className="space-y-2">
                {course.skills.map((s: any) => (
                  <li key={s.id} className="flex items-center gap-2 text-sm text-gray-500">
                    <span className="text-emerald-600">▹</span> {s.name}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 text-sm italic">לא צוינו כישורים ספציפיים.</p>
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-emerald-700 mb-3 border-b border-blue-500/20 pb-2">דרישות קדם</h3>
            {course.prerequisites ? (
              <div className="bg-gray-100 rounded-lg p-4 border border-gray-200">
                <div className="flex flex-col gap-2 relative before:absolute before:left-2.5 before:top-4 before:bottom-4 before:w-0.5 before:bg-gray-100">
                  {course.prerequisites.split(',').map((p: string, i: number) => {
                    const shortCode = parseInt(p.trim());
                    const fullCode = parseInt(`26${shortCode}`);
                    const prereqCourse = courses.find((c: any) => c.course_code === fullCode || c.course_code === shortCode);
                    return (
                      <div key={i} className="flex items-center gap-3 relative z-10">
                        <div className="w-5 h-5 rounded-full bg-orange-500/20 border border-orange-500/50 flex items-center justify-center text-[10px]">P</div>
                        <span className="text-sm text-gray-500">{shortCode}{prereqCourse ? ` - ${prereqCourse.name}` : ''}</span>
                      </div>
                    );
                  })}
                  <div className="flex items-center gap-3 relative z-10 mt-2">
                    <div className="w-5 h-5 rounded-full bg-blue-500/40 border border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] flex items-center justify-center text-[10px]">C</div>
                    <span className="text-sm font-semibold">{course.name}</span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-400 text-sm italic">אין</p>
            )}
          </div>
        </div>

        {course.occurrences?.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-emerald-700 mb-3 border-b border-blue-500/20 pb-2">מועדי הקורס</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {course.occurrences.map((occ: any, i: number) => (
                <div key={i} className="flex items-center gap-3 bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm">
                  <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold shrink-0">
                    {occ.day_of_week?.[0] ?? '?'}
                  </span>
                  <span className="font-medium text-gray-700">{occ.day_of_week}</span>
                  <span className="text-gray-400 mr-auto">{occ.start_time} – {occ.end_time}</span>
                  {occ.room && <span className="text-xs text-gray-400 border border-gray-200 rounded px-1.5 py-0.5">{occ.room}</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <div className="flex justify-between items-center mb-4 border-b border-emerald-500/20 pb-2">
            <h3 className="text-lg font-semibold text-emerald-700">ביקורות סטודנטים</h3>
            <button onClick={onOpenReviews} className="text-sm bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded transition-colors shadow">
              קרא / כתוב ביקורות
            </button>
          </div>
          {loading ? (
            <div className="text-center text-gray-400 text-sm">טוען ביקורות...</div>
          ) : reviews.length === 0 ? (
            <div className="text-center text-gray-400 text-sm italic bg-gray-100 p-6 rounded-xl border border-gray-200">אין ביקורות עדיין. היה הראשון לכתוב!</div>
          ) : (
            <div className="space-y-4 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
              {reviews.map((r, i) => (
                <div key={i} className="bg-gray-100 rounded-xl p-4 border border-gray-200">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-yellow-400">{'⭐'.repeat(r.rating)}</span>
                    <span className="text-gray-400 text-xs">{'⭐'.repeat(5 - r.rating)}</span>
                    <span className="ml-auto text-xs text-emerald-600 font-medium">{r.student_name || `סטודנט #${r.student_id}`}</span>
                  </div>
                  <p className="text-sm text-gray-500">{r.review_text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TimePicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, right: 0 });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const inTrigger = triggerRef.current?.contains(e.target as Node);
      const inDropdown = dropdownRef.current?.contains(e.target as Node);
      if (!inTrigger && !inDropdown) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleToggle = () => {
    if (!open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPos({ top: rect.bottom + 6, right: window.innerWidth - rect.right });
    }
    setOpen(o => !o);
  };

  const slots = Array.from({ length: 28 }, (_, i) => {
    const h = Math.floor(i / 2) + 8;
    const m = i % 2 === 0 ? '00' : '30';
    return `${String(h).padStart(2, '0')}:${m}`;
  });

  return (
    <div className="relative">
      <button ref={triggerRef} type="button" onClick={handleToggle} className="time-picker-btn flex items-center gap-1">
        <svg className="w-3.5 h-3.5 text-gray-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
        <span className={`text-sm ${value ? 'text-gray-700' : 'text-gray-400'}`}>{value || '--:--'}</span>
      </button>
      {open && createPortal(
        <div ref={dropdownRef} style={{ position: 'fixed', top: pos.top, right: pos.right, zIndex: 9999 }}
          className="bg-white rounded-xl shadow-lg border border-gray-200 py-1 max-h-44 overflow-y-auto w-[72px]">
          {value && (
            <button type="button" className="time-picker-clear" onClick={() => { onChange(''); setOpen(false); }}>✕</button>
          )}
          {slots.map(h => (
            <button type="button" key={h} className={`time-picker-option${value === h ? ' selected' : ''}`}
              onClick={() => { onChange(h); setOpen(false); }}>{h}</button>
          ))}
        </div>,
        document.body
      )}
    </div>
  );
}

export default function CourseExplorer() {
  const { user } = useAuth();
  const [courses, setCourses] = useState<any[]>([]);
  const [tracks, setTracks] = useState<any[]>([]);
  const [history, setHistory] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState('');
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);
  const [noMandatoryAttendance, setNoMandatoryAttendance] = useState(false);
  const [lowWorkload, setLowWorkload] = useState(false);
  const [prereqsMetOnly, setPrereqsMetOnly] = useState(false);

  const [selectedDays, setSelectedDays] = useState<Set<string>>(new Set());
  const [timeFrom, setTimeFrom] = useState('');
  const [timeTo, setTimeTo] = useState('');

  const [selectedCourse, setSelectedCourse] = useState<any>(null);
  const [reviewCourse, setReviewCourse] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [coursesRes, metaRes, histRes] = await Promise.all([
          api.getCourses(),
          api.getMetadata(),
          user ? api.getHistory(user.user_id) : { data: [] }
        ]);
        setCourses(coursesRes.data);
        if (metaRes.data?.tracks) setTracks(metaRes.data.tracks);
        setHistory(new Set(histRes.data.map((h: any) => h.course_code)));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);

  const hasPrereqs = (prereqs: string) => {
    if (!prereqs) return true;
    // Assuming simple format like "1001, 1002" or just string matching for now
    // A robust version would parse AST
    const codes = prereqs.match(/\d{4,5}/g) || [];
    return codes.every(c => history.has(parseInt(c)));
  };

  const filteredCourses = courses.filter(c => {
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) || c.course_code.toString().includes(search);
    const matchesTrack = selectedTrack ? c.track_id === selectedTrack : true;
    const matchesAttendance = noMandatoryAttendance ? !c.mandatory_attendance : true;
    const matchesWorkload = lowWorkload ? c.workload <= 3 : true;
    const matchesPrereqs = prereqsMetOnly ? hasPrereqs(c.prerequisites) : true;
    const matchesDayTime = (!selectedDays.size && !timeFrom && !timeTo) ? true :
      c.occurrences?.some((occ: any) => {
        const dayOk = !selectedDays.size || selectedDays.has(occ.day_of_week);
        const timeOk = (!timeFrom || occ.start_time >= timeFrom) && (!timeTo || occ.start_time <= timeTo);
        return dayOk && timeOk;
      });

    return matchesSearch && matchesTrack && matchesAttendance && matchesWorkload && matchesPrereqs && matchesDayTime;
  });

  return (
    <div className="w-full min-w-0 space-y-6 animate-fade-in">
      {/* Header and Visual Track Navigator */}
      <div className="glass-panel !p-6">
        <h1 className="text-2xl sm:text-3xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500">חיפוש קורסים</h1>
        
        <div className="flex flex-wrap gap-3 mb-6">
          <button
            onClick={() => setSelectedTrack(null)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${selectedTrack === null ? 'bg-emerald-600 text-gray-800 shadow-[0_0_15px_rgba(37,99,235,0.4)]' : 'bg-gray-100 text-gray-500 hover:bg-gray-100'}`}
          >
            כל המסלולים
          </button>
          {tracks.map(t => (
            <button
              key={t.id}
              onClick={() => setSelectedTrack(t.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${selectedTrack === t.id ? 'bg-emerald-600 text-gray-800 shadow-[0_0_15px_rgba(37,99,235,0.4)]' : 'bg-gray-100 text-gray-500 hover:bg-gray-100'}`}
            >
              {t.name}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="חפש לפי שם או קוד..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-white border border-gray-200 rounded-xl px-4 py-2.5 text-gray-900 placeholder-gray-400 focus:outline-none focus:border-emerald-400 transition-colors mb-4 shadow-sm"
        />

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5">
            {[['ראשון','א'],['שני','ב'],['שלישי','ג'],['רביעי','ד'],['חמישי','ה']].map(([day, letter]) => (
              <button
                key={day}
                title={day}
                onClick={() => setSelectedDays(prev => { const next = new Set(prev); if (next.has(day)) next.delete(day); else next.add(day); return next; })}
                className={`w-9 h-9 rounded-full text-sm font-bold flex items-center justify-center transition-all duration-150 ${selectedDays.has(day) ? 'bg-emerald-500 text-white shadow-md shadow-emerald-200 scale-110' : 'bg-gray-100 text-gray-500 hover:bg-emerald-50 hover:text-emerald-600 hover:scale-105'}`}
              >{letter}</button>
            ))}
          </div>

          <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-2.5 h-9">
            <span className="text-xs text-gray-400 select-none font-medium shrink-0">משעה</span>
            <TimePicker value={timeFrom} onChange={setTimeFrom} />
            <div className="w-4 h-px bg-gradient-to-r from-emerald-300 to-emerald-500 shrink-0" />
            <TimePicker value={timeTo} onChange={setTimeTo} />
          </div>
          <div className="h-5 w-px bg-gray-200 mx-0.5" />

          {([
            [noMandatoryAttendance, setNoMandatoryAttendance, 'ללא נוכחות חובה'],
            [lowWorkload, setLowWorkload, 'עומס נמוך'],
            [prereqsMetOnly, setPrereqsMetOnly, 'תנאי קדם מולאו'],
          ] as [boolean, (v: boolean) => void, string][]).map(([val, setter, label]) => (
            <button key={label} onClick={() => setter(!val)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 ${val ? 'bg-emerald-500 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900'}`}
            >{label}</button>
          ))}

          {(selectedDays.size > 0 || timeFrom || timeTo || noMandatoryAttendance || lowWorkload || prereqsMetOnly) && (
            <button
              onClick={() => { setSelectedDays(new Set()); setTimeFrom(''); setTimeTo(''); setNoMandatoryAttendance(false); setLowWorkload(false); setPrereqsMetOnly(false); }}
              className="mr-auto px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-400 hover:bg-red-100 hover:text-red-600 transition-all duration-150"
            >נקה הכל ✕</button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6">
          {filteredCourses.map(course => (
            <div 
              key={course.course_code} 
              onClick={() => setSelectedCourse(course)}
              className="glass-panel !p-6 flex flex-col h-full cursor-pointer hover:-translate-y-1 hover:border-blue-500/50 hover:shadow-[0_10px_30px_rgba(37,99,235,0.2)] transition-all duration-300"
            >
              <div className="flex justify-between items-start mb-4">
                <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-emerald-700">
                  {course.course_code}
                </span>
                {course.mandatory_attendance && (
                  <span className="text-[10px] uppercase tracking-wider bg-red-500/20 text-red-300 px-2 py-1 rounded border border-red-500/30">
                    חובה
                  </span>
                )}
              </div>
              <h3 className="text-xl font-semibold mb-2 flex-grow">{course.name}</h3>
              
              <div className="text-sm text-gray-500 mb-4 space-y-1">
                <p>עומס: <span className="text-gray-800">{course.workload} שעות בשבוע</span></p>
                {course.prerequisites && (
                  <p className="truncate">דרישות קדם: <span className="text-orange-300">
                    {course.prerequisites.split(',').map((p: string, i: number) => {
                      const shortCode = parseInt(p.trim());
                      const fullCode = parseInt(`26${shortCode}`);
                      const prereq = courses.find((c: any) => c.course_code === fullCode || c.course_code === shortCode);
                      return (i > 0 ? ', ' : '') + shortCode + (prereq ? ` - ${prereq.name}` : '');
                    }).join('')}
                  </span></p>
                )}
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                <span className="text-xs border border-gray-200 bg-gray-100 px-2 py-1 rounded-full text-gray-500">
                  עומס: {course.workload}
                </span>
                <span className="text-xs border border-gray-200 bg-gray-100 px-2 py-1 rounded-full text-gray-500">
                  נוכחות: {course.mandatory_attendance ? 'חובה' : 'גמיש'}
                </span>
                <span className="text-xs border border-teal-200 bg-teal-50 px-2 py-1 rounded-full text-teal-700">
                  {course.day_of_week || 'טרם נקבע'} {course.start_time ? `${course.start_time}-${course.end_time}` : ''}
                </span>
              </div>

              {course.skills?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-auto pt-4 border-t border-gray-200">
                  {course.skills.slice(0,3).map((s: any) => (
                    <span key={s.id} className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-500">
                      {s.name}
                    </span>
                  ))}
                  {course.skills.length > 3 && <span className="text-xs text-gray-400">+{course.skills.length - 3}</span>}
                </div>
              )}
            </div>
          ))}
          {filteredCourses.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-400">
              לא נמצאו קורסים התואמים את הסינון שלך.
            </div>
          )}
        </div>
      )}

      {selectedCourse && (
        <CourseModal
          course={selectedCourse}
          courses={courses}
          onClose={() => setSelectedCourse(null)}
          onOpenReviews={() => {
            setReviewCourse(selectedCourse);
            setSelectedCourse(null);
          }}
        />
      )}

      {reviewCourse && (
        <ReviewModal course={reviewCourse} onClose={() => setReviewCourse(null)} />
      )}
    </div>
  );
}
