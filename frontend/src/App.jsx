import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './modules/dashboard/pages/Dashboard';
import QuoteList from './modules/quote/pages/QuoteList';
import QuoteEditor from './modules/quote/pages/QuoteEditor';
import ProductsManager from './modules/quote/pages/ProductsManager';
import InspectorList from './modules/inspector/pages/InspectorList';
import WizardPage from './modules/inspector/pages/WizardPage';
import MathList from './modules/math/pages/MathList';
import CalculoWizardPage from './modules/math/pages/CalculoWizardPage';
import ListEditor from './modules/list/pages/ListEditor';
import ListDocumentList from './modules/list/pages/ListDocumentList';
import PlannerList from './modules/planner/pages/PlannerList';
import PlannerDetail from './modules/planner/pages/PlannerDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        
        {/* Rutas con Layout (Sidebar + Header) */}
        <Route element={<Layout />}>
          <Route path="/quote" element={<QuoteList />} />
          <Route path="/quote/new" element={<QuoteEditor />} />
          <Route path="/quote/:id" element={<QuoteEditor />} />
          <Route path="/products" element={<ProductsManager />} />
          
          <Route path="/inspector" element={<InspectorList />} />
          <Route path="/inspector/new" element={<WizardPage />} />

          <Route path="/math" element={<MathList />} />
          <Route path="/math/new" element={<CalculoWizardPage />} />

          <Route path="/list" element={<ListDocumentList />} />
          <Route path="/list/new" element={<ListEditor />} />
          <Route path="/list/:id" element={<ListEditor />} />

          <Route path="/planner" element={<PlannerList />} />
          <Route path="/planner/:id" element={<PlannerDetail />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
