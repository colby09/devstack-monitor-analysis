import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Instances from './pages/Instances'
import DumpedRAM from './pages/DumpedRAM'
import Forensics from './pages/Forensics'
import Services from './pages/Services'
import Metrics from './pages/Metrics'
import Settings from './pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/instances" element={<Instances />} />
        <Route path="/dumps" element={<DumpedRAM />} />
        <Route path="/forensics" element={<Forensics />} />
        <Route path="/services" element={<Services />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App