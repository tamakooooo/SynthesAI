import { Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import ConfigPage from './pages/ConfigPage';
import LoginPage from './pages/LoginPage';

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/config" element={<ConfigPage />} />
      </Routes>
    </MainLayout>
  );
}

export default App;
