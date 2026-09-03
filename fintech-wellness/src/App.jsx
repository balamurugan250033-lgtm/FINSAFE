import { useState } from 'react';
import { customerList, customerMap } from './data/customers';
import ConsentScreen from './components/ConsentScreen';
import Dashboard from './components/Dashboard';
import FlagDetail from './components/FlagDetail';
import Intervention from './components/Intervention';
import Header from './components/Header';

export default function App() {
  const [screen, setScreen] = useState('consent');
  const [selectedId, setSelectedId] = useState('healthy');
  const [monitoringOn, setMonitoringOn] = useState(false);

  const selectedCustomer = customerMap[selectedId];

  const handleAcceptConsent = (enabled) => {
    setMonitoringOn(enabled);
    setScreen('dashboard');
  };

  const handleShowDetails = () => setScreen('detail');
  const handleBackToDashboard = () => setScreen('dashboard');
  const handleShowInterventionFromDetail = () => setScreen('intervention');

  const renderScreen = () => {
    switch (screen) {
      case 'consent':
        return <ConsentScreen onAccept={handleAcceptConsent} />;
      case 'dashboard':
        return (
          <Dashboard
            customers={customerList}
            selectedId={selectedId}
            onSelect={setSelectedId}
            monitoringOn={monitoringOn}
            onShowDetails={handleShowDetails}
          />
        );
      case 'detail':
        return (
          <FlagDetail
            customer={selectedCustomer}
            onBack={handleBackToDashboard}
            onShowIntervention={handleShowInterventionFromDetail}
          />
        );
      case 'intervention':
        return <Intervention onBack={handleBackToDashboard} />;
      default:
        return <ConsentScreen onAccept={handleAcceptConsent} />;
    }
  };

  return (
    <div
      className={`
        mx-auto flex min-h-screen w-full max-w-sm flex-col
        bg-gray-50 text-gray-900
      `}
    >
      {screen !== 'consent' && (
        <Header
          title="Financial Wellness Monitor"
          monitoringOn={monitoringOn}
          onToggleMonitoring={setMonitoringOn}
        />
      )}
      <main className="flex-1 pb-20">{renderScreen()}</main>
    </div>
  );
}
