import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../services/api';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import EmailCard from '../components/EmailCard';
import AIInsights from '../components/AIInsights';

export default function Dashboard() {
  const navigate = useNavigate();
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState('inbox'); // 'inbox' or 'spam'
  
  // Accounts management
  const [accounts, setAccounts] = useState([]);
  const [activeEmailFilter, setActiveEmailFilter] = useState(null); // null means Unified (All)
  const [refreshedTokensCount, setRefreshedTokensCount] = useState(0);

  // Filters
  const [showAll, setShowAll] = useState(false); // false: show unread only, true: show all
  const [selectedPriorityFilter, setSelectedPriorityFilter] = useState('All'); // 'All', 'Critical', 'High', 'Medium', 'Low'

  // Notifications
  const [notifications, setNotifications] = useState([]);

  // Rules Settings Dialog state
  const [isRulesOpen, setIsRulesOpen] = useState(false);
  const [rulesConfig, setRulesConfig] = useState({
    vip_senders: [],
    domains: [],
    keywords: [],
    custom_senders: [],
    custom_keywords: [],
    preference_boosts: { inbox_boost: 0, spam_boost: 0 }
  });
  const [newCustomSender, setNewCustomSender] = useState('');
  const [newCustomKeyword, setNewCustomKeyword] = useState('');
  const [isSavingRules, setIsSavingRules] = useState(false);

  // Load connected accounts from local storage
  const loadAccounts = () => {
    let list = [];
    try {
      const stored = localStorage.getItem('aeroinbox_accounts');
      list = stored ? JSON.parse(stored) : [];
    } catch (e) {
      list = [];
    }
    
    // Backward compatibility check
    const legacyToken = localStorage.getItem('google_access_token');
    const legacyEmail = localStorage.getItem('user_email');
    const legacyRefresh = localStorage.getItem('google_refresh_token') || '';
    
    if (list.length === 0 && legacyToken && legacyEmail) {
      const defaultAcc = {
        email: legacyEmail,
        access_token: legacyToken,
        refresh_token: legacyRefresh
      };
      list = [defaultAcc];
      localStorage.setItem('aeroinbox_accounts', JSON.stringify(list));
    }
    setAccounts(list);
    return list;
  };

  const fetchEmails = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = loadAccounts();
      if (list.length === 0) {
        navigate('/');
        return;
      }

      // API request to post accounts and retrieve prioritized emails
      const response = await API.post('/emails/unread', {
        accounts: list,
        include_read: showAll
      });

      const fetchedEmails = response.data?.emails || [];
      setEmails(fetchedEmails);

      // Generate in-app notifications from unread emails
      const newNotifs = [];
      fetchedEmails.forEach(email => {
        if (email.read_status === 'unread') {
          if (email.final_priority === 'Critical') {
            newNotifs.push({
              type: 'Critical',
              subject: email.subject,
              sender: email.sender,
              email: email
            });
          }
          if (email.folder === 'SPAM' && email.ai_analysis?.is_spam_false_positive) {
            newNotifs.push({
              type: 'Spam Alert',
              subject: email.subject,
              sender: email.sender,
              email: email
            });
          } else if (email.ai_analysis?.is_meeting_request) {
            newNotifs.push({
              type: 'Meeting',
              subject: email.subject,
              sender: email.sender,
              email: email
            });
          }
        }
      });
      setNotifications(newNotifs);
      
      // Auto-select the first email from the filtered view
      const firstEmail = getFilteredEmails(fetchedEmails)[0];
      if (firstEmail) {
        setSelectedEmail(firstEmail);
      } else {
        setSelectedEmail(null);
      }
    } catch (err) {
      console.error('Error fetching emails:', err);
      const errMsg = err.response?.data?.detail || err.message || 'Please try again.';
      setError(`Failed to retrieve emails: ${errMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadRules = async () => {
    try {
      const response = await API.get('/emails/config/rules');
      if (response.data) {
        setRulesConfig(response.data);
      }
    } catch (err) {
      console.error('Error loading rules configuration:', err);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('google_access_token');
    if (!token) {
      navigate('/');
    } else {
      fetchEmails();
      loadRules();
    }
  }, [navigate, showAll]);

  // Swapping theme or filter updates account lists
  const handleSwitchAccount = (email) => {
    setActiveEmailFilter(email);
    // Auto-select first matching email
    const filtered = emails.filter(e => {
      const matchAcc = !email || e.account_email === email;
      const matchFolder = activeSection === 'inbox' ? e.folder === 'INBOX' : (e.folder === 'SPAM' && e.ai_analysis?.is_spam_false_positive);
      return matchAcc && matchFolder;
    });
    setSelectedEmail(filtered[0] || null);
  };

  // Generic function to filter emails according to state
  const getFilteredEmails = (emailsList = emails) => {
    return emailsList.filter(email => {
      // 1. Account Filter
      if (activeEmailFilter && email.account_email !== activeEmailFilter) {
        return false;
      }
      // 2. Folder Section Filter
      if (activeSection === 'inbox') {
        if (email.folder !== 'INBOX') return false;
      } else if (activeSection === 'spam') {
        // Only show spam false positives
        if (email.folder !== 'SPAM' || !email.ai_analysis?.is_spam_false_positive) return false;
      }
      // 3. Priority Filter
      if (selectedPriorityFilter !== 'All') {
        if (email.final_priority !== selectedPriorityFilter) return false;
      }
      return true;
    });
  };

  const filteredEmailsList = getFilteredEmails();

  // Label Modification actions:
  const handleMarkRead = async (email, read = true) => {
    const acc = accounts.find(a => a.email === email.account_email);
    const token = acc ? acc.access_token : localStorage.getItem('google_access_token');
    
    try {
      const endpoint = read ? `/emails/${email.id}/read` : `/emails/${email.id}/unread`;
      await API.post(endpoint, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Refresh local emails list
      setEmails(prev => prev.map(e => {
        if (e.id === email.id) {
          return { ...e, read_status: read ? 'read' : 'unread' };
        }
        return e;
      }));
      // Update selected email reference
      if (selectedEmail?.id === email.id) {
        setSelectedEmail(prev => ({ ...prev, read_status: read ? 'read' : 'unread' }));
      }
    } catch (err) {
      console.error('Failed to change read status:', err);
    }
  };

  const handleMoveToInbox = async (email) => {
    const acc = accounts.find(a => a.email === email.account_email);
    const token = acc ? acc.access_token : localStorage.getItem('google_access_token');
    
    try {
      await API.post(`/emails/${email.id}/move-to-inbox`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchEmails();
    } catch (err) {
      console.error('Failed to move email to inbox:', err);
    }
  };

  const handleMarkSafe = async (email) => {
    const acc = accounts.find(a => a.email === email.account_email);
    const token = acc ? acc.access_token : localStorage.getItem('google_access_token');
    
    // Strip name bracket to get raw sender email
    const fromStr = email.sender || '';
    const match = fromStr.match(/<([^>]+)>/);
    const senderEmailAddress = match ? match[1] : fromStr;

    try {
      await API.post(`/emails/${email.id}/mark-safe`, {
        sender_email: senderEmailAddress
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Refresh rules configuration and emails
      await loadRules();
      await fetchEmails();
    } catch (err) {
      console.error('Failed to mark sender as safe:', err);
    }
  };

  const handleSaveRules = async () => {
    setIsSavingRules(true);
    try {
      await API.post('/emails/config/rules', rulesConfig);
      setIsRulesOpen(false);
      await fetchEmails(); // Refetch to recalculate scores with updated rules
    } catch (err) {
      console.error('Failed to save rules:', err);
    } finally {
      setIsSavingRules(false);
    }
  };

  const handleAddCustomSender = () => {
    if (newCustomSender.trim() && !rulesConfig.custom_senders.includes(newCustomSender)) {
      setRulesConfig(prev => ({
        ...prev,
        custom_senders: [...prev.custom_senders, newCustomSender.trim().toLowerCase()]
      }));
      setNewCustomSender('');
    }
  };

  const handleRemoveCustomSender = (sender) => {
    setRulesConfig(prev => ({
      ...prev,
      custom_senders: prev.custom_senders.filter(s => s !== sender)
    }));
  };

  const handleAddCustomKeyword = () => {
    if (newCustomKeyword.trim() && !rulesConfig.custom_keywords.includes(newCustomKeyword)) {
      setRulesConfig(prev => ({
        ...prev,
        custom_keywords: [...prev.custom_keywords, newCustomKeyword.trim().toLowerCase()]
      }));
      setNewCustomKeyword('');
    }
  };

  const handleRemoveCustomKeyword = (kw) => {
    setRulesConfig(prev => ({
      ...prev,
      custom_keywords: prev.custom_keywords.filter(k => k !== kw)
    }));
  };

  return (
    <div className="flex h-screen bg-slate-100 dark:bg-[#080b11] overflow-hidden text-slate-800 dark:text-slate-100 font-sans transition-colors duration-150">
      {/* Sidebar navigation */}
      <Sidebar 
        onOpenRules={() => setIsRulesOpen(true)} 
        activeSection={activeSection}
        setActiveSection={(sec) => {
          setActiveSection(sec);
          // Auto select first email in the folder section
          const filtered = emails.filter(e => {
            const matchAcc = !activeEmailFilter || e.account_email === activeEmailFilter;
            const matchFolder = sec === 'inbox' ? e.folder === 'INBOX' : (e.folder === 'SPAM' && e.ai_analysis?.is_spam_false_positive);
            return matchAcc && matchFolder;
          });
          setSelectedEmail(filtered[0] || null);
        }}
      />

      {/* Main content frame */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header toolbar */}
        <Header 
          onRefresh={fetchEmails} 
          isLoading={isLoading} 
          accounts={accounts}
          activeEmail={activeEmailFilter}
          onSwitchAccount={handleSwitchAccount}
          notifications={notifications}
          onSelectEmail={(email) => {
            setSelectedEmail(email);
            // Sync current folder selection to match clicked email
            if (email.folder === 'SPAM') {
              setActiveSection('spam');
            } else {
              setActiveSection('inbox');
            }
          }}
        />

        {/* Dynamic content split panel */}
        <div className="flex-1 flex min-h-0">
          
          {/* LEFT PANEL: Email List Column */}
          <div className="w-[380px] border-r border-slate-200 dark:border-slate-800/60 bg-white dark:bg-[#090d16]/30 flex flex-col min-h-0 transition-colors duration-150">
            {/* Filter Pill Controls bar */}
            <div className="p-3 border-b border-slate-200 dark:border-slate-800/40 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/10">
              <div className="flex items-center space-x-1.5">
                <button
                  onClick={() => setShowAll(false)}
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-all cursor-pointer ${
                    !showAll
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-200/65 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-350'
                  }`}
                >
                  Unread
                </button>
                <button
                  onClick={() => setShowAll(true)}
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-all cursor-pointer ${
                    showAll
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-200/65 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-350'
                  }`}
                >
                  All Mail
                </button>
              </div>

              {/* Priority Select */}
              <select
                value={selectedPriorityFilter}
                onChange={(e) => {
                  setSelectedPriorityFilter(e.target.value);
                  // Reset select
                  setSelectedEmail(null);
                }}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded px-1.5 py-0.5 text-[10px] font-bold text-slate-600 dark:text-slate-300 outline-none"
              >
                <option value="All">All Priorities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>

            {/* List View Container */}
            {isLoading ? (
              <div className="flex-1 flex flex-col items-center justify-center space-y-3">
                <div className="h-7 w-7 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin"></div>
                <span className="text-xs text-slate-500 font-medium">Downloading mailboxes...</span>
              </div>
            ) : error ? (
              <div className="p-6 text-center space-y-3">
                <p className="text-xs text-red-500 dark:text-red-400 font-semibold">{error}</p>
                <button
                  onClick={fetchEmails}
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition-all cursor-pointer"
                >
                  Retry Connection
                </button>
              </div>
            ) : filteredEmailsList.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-slate-400 dark:text-slate-600">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
                </svg>
                <p className="text-xs font-bold text-slate-600 dark:text-slate-400">All caught up!</p>
                <p className="text-[10px] text-slate-400 dark:text-slate-600">No emails match the selected filters.</p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/20">
                {filteredEmailsList.map(email => (
                  <EmailCard
                    key={email.id}
                    email={email}
                    isSelected={selectedEmail?.id === email.id}
                    onClick={() => setSelectedEmail(email)}
                    aiInsights={email.ai_analysis}
                  />
                ))}
              </div>
            )}
          </div>

          {/* RIGHT PANEL: Email Details & AI Insights Column */}
          <div className="flex-1 flex min-w-0 bg-white dark:bg-[#0b0f19]/25 transition-all">
            {selectedEmail ? (
              <>
                {/* Center Column: Email Details */}
                <div className="flex-1 flex flex-col min-w-0 border-r border-slate-200 dark:border-slate-800/60 bg-white dark:bg-transparent">
                  {/* Action Toolbar */}
                  <div className="h-12 px-6 border-b border-slate-200 dark:border-slate-800/40 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/10">
                    <div className="flex items-center space-x-2">
                      {/* Mark Read/Unread Toggle */}
                      {selectedEmail.read_status === 'unread' ? (
                        <button
                          onClick={() => handleMarkRead(selectedEmail, true)}
                          className="px-3 py-1 rounded border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-300 transition-colors cursor-pointer"
                        >
                          Mark as Read
                        </button>
                      ) : (
                        <button
                          onClick={() => handleMarkRead(selectedEmail, false)}
                          className="px-3 py-1 rounded border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-300 transition-colors cursor-pointer"
                        >
                          Mark as Unread
                        </button>
                      )}

                      {/* Spam Folder Intelligence Actions */}
                      {selectedEmail.folder === 'SPAM' && (
                        <>
                          <button
                            onClick={() => handleMoveToInbox(selectedEmail)}
                            className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-[10px] font-bold text-white transition-colors cursor-pointer"
                          >
                            Move to Inbox
                          </button>
                          <button
                            onClick={() => handleMarkSafe(selectedEmail)}
                            className="px-3 py-1 rounded border border-emerald-500/30 hover:bg-emerald-500/10 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 transition-colors cursor-pointer"
                          >
                            Mark Safe Sender
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Sender Details Header */}
                  <div className="p-6 border-b border-slate-200 dark:border-slate-800/60 space-y-3">
                    <div className="flex justify-between items-start">
                      <h1 className="text-sm font-bold text-slate-850 dark:text-white leading-snug">
                        {selectedEmail.subject}
                      </h1>
                      <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                        {new Date(selectedEmail.date).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-slate-405 dark:text-slate-550 font-bold">From:</span>
                      <span className="text-xs text-slate-700 dark:text-slate-300 truncate font-semibold">{selectedEmail.sender}</span>
                    </div>
                  </div>

                  {/* Scrollable Email Body */}
                  <div className="flex-1 p-6 overflow-y-auto bg-white dark:bg-transparent">
                    {selectedEmail.body ? (
                      <pre className="whitespace-pre-wrap font-sans text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                        {selectedEmail.body}
                      </pre>
                    ) : (
                      <p className="text-xs text-slate-400 dark:text-slate-650 italic">No email body content available.</p>
                    )}
                  </div>
                </div>

                {/* Right Column: AI Insights Pane */}
                <div className="w-[380px] bg-slate-50 dark:bg-slate-900/10">
                  <AIInsights
                    insights={selectedEmail.ai_analysis}
                    isLoading={false}
                    folder={selectedEmail.folder}
                  />
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className="w-10 h-10 text-slate-300 dark:text-slate-700 animate-bounce">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 9v.906a2.25 2.25 0 0 1-1.183 1.981l-6.478 3.488M2.25 9v.906a2.25 2.25 0 0 0 1.183 1.981l6.478 3.488m8.839 2.51-4.66-2.51m0 0-1.023-.55a2.25 2.25 0 0 0-2.134 0l-1.022.55m0 0-4.661 2.51m16.5 1.615V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5a2.25 2.25 0 0 0 2.25 2.25h15a2.25 2.25 0 0 0 2.25-2.25Z" />
                </svg>
                <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">Select an email to read details</p>
                <p className="text-xs text-slate-400 dark:text-slate-600">Choose any item from the left column to display priority analyses.</p>
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Rules Customization Dialog Modal */}
      {isRulesOpen && (
        <div className="fixed inset-0 bg-slate-950/60 dark:bg-black/70 flex items-center justify-center p-6 z-50 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#0c121e] rounded-2xl border border-slate-200 dark:border-slate-800 w-full max-w-2xl shadow-2xl p-6 overflow-hidden flex flex-col max-h-[85vh]">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3.5 mb-4">
              <h3 className="text-base font-bold text-slate-800 dark:text-white">Configure Prioritization Rules</h3>
              <button 
                onClick={() => setIsRulesOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-5 pr-1">
              
              {/* Custom sender VIPs list */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Custom VIP Senders</label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="email@example.com or name snippet"
                    value={newCustomSender}
                    onChange={(e) => setNewCustomSender(e.target.value)}
                    className="flex-1 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-xs outline-none focus:border-indigo-500"
                  />
                  <button 
                    onClick={handleAddCustomSender}
                    className="px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-500 cursor-pointer"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {rulesConfig.custom_senders.length === 0 ? (
                    <span className="text-[10px] text-slate-400 italic">No custom senders added yet.</span>
                  ) : (
                    rulesConfig.custom_senders.map((sender, idx) => (
                      <span key={idx} className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700/50">
                        <span>{sender}</span>
                        <button onClick={() => handleRemoveCustomSender(sender)} className="hover:text-red-500 text-[9px] font-extrabold ml-1 cursor-pointer">✕</button>
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* Custom keywords lists */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Custom Priority Keywords</label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="urgent word or category tag"
                    value={newCustomKeyword}
                    onChange={(e) => setNewCustomKeyword(e.target.value)}
                    className="flex-1 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-xs outline-none focus:border-indigo-500"
                  />
                  <button 
                    onClick={handleAddCustomKeyword}
                    className="px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-500 cursor-pointer"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {rulesConfig.custom_keywords.length === 0 ? (
                    <span className="text-[10px] text-slate-400 italic">No custom keywords added yet.</span>
                  ) : (
                    rulesConfig.custom_keywords.map((kw, idx) => (
                      <span key={idx} className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700/50">
                        <span>{kw}</span>
                        <button onClick={() => handleRemoveCustomKeyword(kw)} className="hover:text-red-500 text-[9px] font-extrabold ml-1 cursor-pointer">✕</button>
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* Folder Boost sliders */}
              <div className="space-y-4 pt-2">
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Priority Preference Boosts</label>
                
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-600 dark:text-slate-350">Inbox Folder Boost score</span>
                    <span className="text-indigo-600 dark:text-indigo-400 font-extrabold">{rulesConfig.preference_boosts.inbox_boost} pts</span>
                  </div>
                  <input
                    type="range"
                    min="-30"
                    max="30"
                    value={rulesConfig.preference_boosts.inbox_boost}
                    onChange={(e) => setRulesConfig(prev => ({
                      ...prev,
                      preference_boosts: { ...prev.preference_boosts, inbox_boost: parseInt(e.target.value) }
                    }))}
                    className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-600 dark:text-slate-350">Spam False-Positive Boost score</span>
                    <span className="text-indigo-600 dark:text-indigo-400 font-extrabold">{rulesConfig.preference_boosts.spam_boost} pts</span>
                  </div>
                  <input
                    type="range"
                    min="-30"
                    max="30"
                    value={rulesConfig.preference_boosts.spam_boost}
                    onChange={(e) => setRulesConfig(prev => ({
                      ...prev,
                      preference_boosts: { ...prev.preference_boosts, spam_boost: parseInt(e.target.value) }
                    }))}
                    className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                </div>
              </div>

              {/* Standard active rules lists */}
              <div className="pt-2.5 border-t border-slate-100 dark:border-slate-800 space-y-3">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Standard Active Rules</span>
                <div className="grid grid-cols-2 gap-4 text-[10px] font-semibold text-slate-500 dark:text-slate-450">
                  <div>
                    <span className="font-bold text-slate-600 dark:text-slate-400 block mb-1">Standard VIPs (+30 pts)</span>
                    <div className="flex flex-wrap gap-1">
                      {rulesConfig.vip_senders.map((v, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">{v}</span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="font-bold text-slate-600 dark:text-slate-400 block mb-1">Target Domains (+20 pts)</span>
                    <div className="flex flex-wrap gap-1">
                      {rulesConfig.domains.map((d, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">@{d}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <div className="flex justify-end space-x-2.5 border-t border-slate-100 dark:border-slate-800 pt-4 mt-4">
              <button
                onClick={() => setIsRulesOpen(false)}
                className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-600 dark:text-slate-350 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRules}
                disabled={isSavingRules}
                className="px-4.5 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-lg shadow-indigo-500/10"
              >
                {isSavingRules ? 'Saving...' : 'Apply Rules'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
