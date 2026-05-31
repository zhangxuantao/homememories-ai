import { Suspense, lazy } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import MobileNav from './components/layout/MobileNav';
import DesktopRail from './components/layout/DesktopRail';

const HomePage = lazy(() => import('./pages/HomePage'));
const TimelinePage = lazy(() => import('./pages/TimelinePage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const PeoplePage = lazy(() => import('./pages/PeoplePage'));
const PhotoDetail = lazy(() => import('./pages/PhotoDetail'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'));
const AlbumsPage = lazy(() => import('./pages/AlbumsPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

function AnimatedPage({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.2 }}
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-white">
      <DesktopRail />
      <main className="md:ml-14 pb-14 md:pb-0">
        <AnimatePresence mode="wait">
          <Suspense fallback={<PageLoader />}>
            <Routes location={location} key={location.pathname}>
              <Route path="/" element={<AnimatedPage><HomePage /></AnimatedPage>} />
              <Route path="/timeline" element={<AnimatedPage><TimelinePage /></AnimatedPage>} />
              <Route path="/search" element={<AnimatedPage><SearchPage /></AnimatedPage>} />
              <Route path="/people" element={<AnimatedPage><PeoplePage /></AnimatedPage>} />
              <Route path="/photo/:id" element={<PhotoDetail />} />
              <Route path="/favorites" element={<AnimatedPage><FavoritesPage /></AnimatedPage>} />
              <Route path="/settings" element={<AnimatedPage><SettingsPage /></AnimatedPage>} />
              <Route path="/albums" element={<AnimatedPage><AlbumsPage /></AnimatedPage>} />
            </Routes>
          </Suspense>
        </AnimatePresence>
      </main>
      <MobileNav />
    </div>
  );
}
