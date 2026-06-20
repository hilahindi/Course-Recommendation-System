import { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  courseModalOverlayClass,
  courseModalShellClass,
  CourseModalCloseButton,
  CourseModalHeader,
  CourseReviewsActionsBar,
  CourseReviewsList,
  CourseSkillsPrerequisitesGrid,
} from './courseDetailUi';

interface CourseDetailModalProps {
  course: any;
  onClose: () => void;
  onOpenReviews: () => void;
  onAddToList?: (course: any) => void;
  showAddToList?: boolean;
}

export default function CourseDetailModal({
  course,
  onClose,
  onOpenReviews,
  onAddToList,
  showAddToList = true,
}: CourseDetailModalProps) {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCourseReviews(course.course_code)
      .then(res => setReviews(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [course.course_code]);

  return (
    <div className={courseModalOverlayClass}>
      <div className={`${courseModalShellClass} custom-scrollbar`}>
        <CourseModalCloseButton onClose={onClose} />

        <CourseModalHeader course={course} />
        <CourseSkillsPrerequisitesGrid course={course} />

        <div>
          <CourseReviewsActionsBar
            course={course}
            onOpenReviews={onOpenReviews}
            onAddToList={onAddToList}
            showAddToList={showAddToList}
          />
          <CourseReviewsList reviews={reviews} loading={loading} />
        </div>
      </div>
    </div>
  );
}
