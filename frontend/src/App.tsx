import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import MobileNav from './components/layout/MobileNav';
import DesktopRail from './components/layout/DesktopRail';

const HomePage = lazy(() => import('./pages/HomePage'));
const TimelinePage = lazy(() => import('./pages/TimelinePage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const PeoplePage = lazy(() => import('./pages/PeoplePage'));
const PhotoDetail = lazy(() => import('./pages/PhotoDetail'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-white">
      <DesktopRail />
      <main className="md:ml-14 pb-14 md:pb-0">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/people" element={<PeoplePage />} />
            <Route path="/photo/:id" element={<PhotoDetail />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Suspense>
      </main>
      <MobileNav />
    </div>
  );
}
