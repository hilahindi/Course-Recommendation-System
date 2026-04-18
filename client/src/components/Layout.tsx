import { ReactNode } from 'react';
import Navbar from './Navbar';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen w-full flex flex-col font-outfit text-white">
      <Navbar />
      <main className="flex-grow p-4 md:p-8 flex justify-center">
        <div className="w-full max-w-6xl">
          {children}
        </div>
      </main>
    </div>
  );
}
