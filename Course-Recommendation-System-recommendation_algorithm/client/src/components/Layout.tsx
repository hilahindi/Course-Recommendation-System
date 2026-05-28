import type { ReactNode } from 'react';
import Navbar from './Navbar';
import { FLUID_CONTAINER } from '../lib/layout';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen w-full flex flex-col font-outfit text-gray-800 box-border">
      {/* Full viewport width — never inside a page-specific max-width wrapper */}
      <header className="sticky top-0 left-0 right-0 z-50 w-full shrink-0">
        <div className="w-full box-border">
          <div className={`${FLUID_CONTAINER} pt-4 pb-3 sm:pt-5 sm:pb-4`}>
            <Navbar />
          </div>
        </div>
      </header>

      <main className="flex-grow w-full min-w-0">
        <div className={`${FLUID_CONTAINER} pb-8 sm:pb-10 lg:pb-12`}>{children}</div>
      </main>
    </div>
  );
}
