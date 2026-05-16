import type { ReactNode } from 'react';
import Navbar from './Navbar';
import { FLUID_CONTAINER, FLUID_CONTAINER_NAV } from '../lib/layout';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen w-full min-w-0 flex flex-col font-outfit text-gray-800 box-border">
      <header className="sticky top-0 z-50 w-full shrink-0">
        <div className={`${FLUID_CONTAINER_NAV} py-3 sm:py-4`}>
          <Navbar />
        </div>
      </header>
      <main className="flex-grow w-full min-w-0">
        <div className={`${FLUID_CONTAINER} pb-8 sm:pb-10 lg:pb-12`}>{children}</div>
      </main>
    </div>
  );
}
