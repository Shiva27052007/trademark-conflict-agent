import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NewScreening from './pages/NewScreening';
import ScreeningResults from './pages/ScreeningResults';
import History from './pages/History';
import ReviewPage from './pages/ReviewPage';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/screen" element={<NewScreening />} />
        <Route path="/screen/:id" element={<ScreeningResults />} />
        <Route path="/history" element={<History />} />
        <Route path="/review/:id" element={<ReviewPage />} />
      </Routes>
    </Layout>
  );
}
