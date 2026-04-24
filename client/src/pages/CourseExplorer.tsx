import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import ReviewModal from '../components/ReviewModal';

function CourseModal({ course, onClose, onOpenReviews }: { course: any, onClose: () => void, onOpenReviews: () => void }) {
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
                  {course.prerequisites.split(',').map((p: string, i: number) => (
                    <div key={i} className="flex items-center gap-3 relative z-10">
                      <div className="w-5 h-5 rounded-full bg-orange-500/20 border border-orange-500/50 flex items-center justify-center text-[10px]">P</div>
                      <span className="text-sm text-gray-500">{p.trim()}</span>
                    </div>
                  ))}
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
    
    return matchesSearch && matchesTrack && matchesAttendance && matchesWorkload && matchesPrereqs;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header and Visual Track Navigator */}
      <div className="glass-panel !p-6">
        <h1 className="text-3xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500">חיפוש קורסים</h1>
        
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

        <div className="flex flex-col md:flex-row gap-4 items-center bg-gray-100 p-4 rounded-xl border border-gray-200">
          <div className="w-full md:w-1/3">
            <input 
              type="text" 
              placeholder="חפש לפי שם או קוד..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-gray-100 border border-gray-200 rounded-lg px-4 py-2 text-gray-800 placeholder-white/40 focus:outline-none focus:border-emerald-400 focus:bg-gray-100 transition-colors m-0"
            />
          </div>
          <div className="flex-grow flex flex-wrap items-center gap-4 text-sm">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input type="checkbox" checked={noMandatoryAttendance} onChange={e => setNoMandatoryAttendance(e.target.checked)} className="form-checkbox bg-black border-gray-200 text-blue-500 rounded focus:ring-0" />
              <span className="text-gray-500 group-hover:text-gray-800 transition-colors">ללא נוכחות חובה</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input type="checkbox" checked={lowWorkload} onChange={e => setLowWorkload(e.target.checked)} className="form-checkbox bg-black border-gray-200 text-blue-500 rounded focus:ring-0" />
              <span className="text-gray-500 group-hover:text-gray-800 transition-colors">עומס נמוך</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input type="checkbox" checked={prereqsMetOnly} onChange={e => setPrereqsMetOnly(e.target.checked)} className="form-checkbox bg-black border-gray-200 text-blue-500 rounded focus:ring-0" />
              <span className="text-gray-500 group-hover:text-gray-800 transition-colors">דרישות קדם מולאו</span>
            </label>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                  <p className="truncate">דרישות קדם: <span className="text-orange-300">{course.prerequisites}</span></p>
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
