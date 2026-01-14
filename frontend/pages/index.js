import React, { useState, useRef } from "react";
import axios from "axios";
import * as XLSX from "xlsx";
import html2canvas from "html2canvas";
import SavedReportsSidebar from "../components/SavedReportsSidebar";
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  IconButton,
  Fab,
} from "@mui/material";
import {
  Send as SendIcon,
  Download as DownloadIcon,
  Code as CodeIcon,
  TableChart as TableChartIcon,
  PieChart as PieChartIcon,
  Close as CloseIcon,
  Image as ImageIcon,
  BookmarkBorder as BookmarkIcon,
  Save as SaveIcon,
  Menu as MenuIcon,
} from "@mui/icons-material";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

export default function Home() {
  // User ID - in production, get from auth system
  const USER_ID = "frontend_user_123";
  
  const [question, setQuestion] = useState("");
  const [sql, setSql] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [showNoDataAlert, setShowNoDataAlert] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Saved Reports state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [reportName, setReportName] = useState("");
  const [reportDescription, setReportDescription] = useState("");
  const [reportTags, setReportTags] = useState("");
  const [currentReportName, setCurrentReportName] = useState("");
  
  // Visualization state
  const [openViz, setOpenViz] = useState(false);
  const [categoryColumn, setCategoryColumn] = useState("");
  const [valueColumn, setValueColumn] = useState("");
  const [aggregation, setAggregation] = useState("SUM");
  const [topN, setTopN] = useState(10);
  const chartRef = useRef(null);

  const COLORS = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe', 
    '#43e97b', '#fa709a', '#fee140', '#30cfd0',
    '#a8edea', '#fed6e3', '#c471f5', '#fa7e61'
  ];

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setWarning("");
    setSql("");
    setRows([]);

    try {
      const res = await axios.post("http://localhost:8000/api/v1/query", {
        question,
        max_rows: 500,
      });

      setSql(res.data.query.sql);
      setRows(res.data.rows);
      setPage(0);
      setShowNoDataAlert(true); // Reset alert visibility when new query runs
      if (res.data.warning) {
        setWarning(res.data.warning);
      }
      
      // Auto-select columns for visualization
      if (res.data.rows.length > 0) {
        const columns = Object.keys(res.data.rows[0]);
        const categorical = columns.find(col => 
          typeof res.data.rows[0][col] === 'string' || 
          col.includes('code') || col.includes('name') || col.includes('id')
        );
        const numerical = columns.find(col => 
          typeof res.data.rows[0][col] === 'number' && 
          !col.includes('id') && !col.includes('code')
        );
        
        if (categorical) setCategoryColumn(categorical);
        if (numerical) setValueColumn(numerical);
      }
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e.message;
      setError(errorMsg);
    }

    setLoading(false);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const downloadExcel = () => {
    if (rows.length === 0) return;
    const worksheet = XLSX.utils.json_to_sheet(rows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Results");
    const timestamp = new Date().toISOString().split('T')[0];
    XLSX.writeFile(workbook, `query_results_${timestamp}.xlsx`);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  };

  const openVisualization = () => {
    setOpenViz(true);
  };

  const closeVisualization = () => {
    setOpenViz(false);
  };

  const downloadChart = async () => {
    if (chartRef.current) {
      const canvas = await html2canvas(chartRef.current);
      const link = document.createElement('a');
      link.download = 'chart.png';
      link.href = canvas.toDataURL();
      link.click();
    }
  };

  // Save Report Functions
  const openSaveDialog = () => {
    setSaveDialogOpen(true);
    // Leave report name empty for user to enter
    setReportName("");
    // Auto-fill description with the question
    setReportDescription(question);
  };

  const closeSaveDialog = () => {
    setSaveDialogOpen(false);
    setReportName("");
    setReportDescription("");
    setReportTags("");
  };

  const saveReport = async () => {
    if (!reportName.trim()) {
      alert("Please enter a report name");
      return;
    }

    try {
      const tagsArray = reportTags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag);

      await axios.post("http://localhost:8000/api/v1/reports", {
        report_name: reportName,
        user_question: question,
        generated_sql: sql,
        user_id: USER_ID,
        report_description: reportDescription || null,
        tags: tagsArray,
        is_favorite: false
      });

      alert("Report saved successfully!");
      closeSaveDialog();
    } catch (err) {
      alert("Failed to save report: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleExecuteSavedReport = (reportData) => {
    setCurrentReportName(reportData.reportName);
    setQuestion(reportData.userQuestion || reportData.reportName); // ← FIX: Use userQuestion!
    setSql(reportData.sql);
    setRows(reportData.rows);
    setPage(0);
    setError("");
    
    // Auto-select columns for visualization
    if (reportData.rows.length > 0) {
      const columns = Object.keys(reportData.rows[0]);
      const categorical = columns.find(col => 
        typeof reportData.rows[0][col] === 'string' || 
        col.includes('code') || col.includes('name') || col.includes('id')
      );
      const numerical = columns.find(col => 
        typeof reportData.rows[0][col] === 'number' && 
        !col.includes('id') && !col.includes('code')
      );
      
      if (categorical) setCategoryColumn(categorical);
      if (numerical) setValueColumn(numerical);
    }
    
    // Close sidebar after executing report
    setSidebarOpen(false);
  };

  const prepareChartData = () => {
    if (!rows.length || !categoryColumn || !valueColumn) return [];

    const grouped = {};
    
    rows.forEach(row => {
      const category = String(row[categoryColumn] || 'Unknown');
      const value = parseFloat(row[valueColumn]) || 0;
      
      if (!grouped[category]) {
        grouped[category] = { values: [], count: 0 };
      }
      grouped[category].values.push(value);
      grouped[category].count++;
    });

    let chartData = Object.keys(grouped).map(category => {
      const values = grouped[category].values;
      let aggregatedValue;
      
      switch (aggregation) {
        case 'SUM':
          aggregatedValue = values.reduce((a, b) => a + b, 0);
          break;
        case 'AVG':
          aggregatedValue = values.reduce((a, b) => a + b, 0) / values.length;
          break;
        case 'COUNT':
          aggregatedValue = grouped[category].count;
          break;
        case 'MAX':
          aggregatedValue = Math.max(...values);
          break;
        case 'MIN':
          aggregatedValue = Math.min(...values);
          break;
        default:
          aggregatedValue = values.reduce((a, b) => a + b, 0);
      }
      
      return {
        name: category,
        value: aggregatedValue
      };
    });

    // Sort and get top N
    chartData.sort((a, b) => b.value - a.value);
    
    if (chartData.length > topN) {
      const topData = chartData.slice(0, topN);
      const othersValue = chartData.slice(topN).reduce((sum, item) => sum + item.value, 0);
      if (othersValue > 0) {
        topData.push({ name: 'Others', value: othersValue });
      }
      chartData = topData;
    }

    // Calculate percentages
    const total = chartData.reduce((sum, item) => sum + item.value, 0);
    chartData.forEach(item => {
      item.percentage = ((item.value / total) * 100).toFixed(1);
    });

    return chartData;
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 2 }}>
          <Typography variant="body2" fontWeight="bold">
            {payload[0].name}
          </Typography>
          <Typography variant="body2" color="primary">
            Value: {payload[0].value.toLocaleString()}
          </Typography>
          <Typography variant="body2" color="secondary">
            Percentage: {payload[0].payload.percentage}%
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  const paginatedRows = rows.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  const chartData = prepareChartData();
  
  const categoricalColumns = columns.filter(col => {
    if (rows.length === 0) return false;
    const firstValue = rows[0][col];
    return typeof firstValue === 'string' || col.includes('code') || col.includes('name') || col.includes('id');
  });
  
  const numericalColumns = columns.filter(col => {
    if (rows.length === 0) return false;
    const firstValue = rows[0][col];
    return typeof firstValue === 'number' && !col.includes('id') && !col.includes('code');
  });

  return (
    <Box sx={{ bgcolor: "#f5f7fa", minHeight: "100vh", py: 4 }}>
      {/* Floating Action Button for Sidebar */}
      <Fab
        color="primary"
        sx={{
          position: "fixed",
          top: 20,
          left: 20,
          zIndex: 1200,
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        }}
        onClick={() => setSidebarOpen(true)}
      >
        <MenuIcon />
      </Fab>

      {/* Saved Reports Sidebar */}
      <SavedReportsSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onExecuteReport={handleExecuteSavedReport}
      />

      <Container maxWidth="xl">
        {/* Header */}
        <Paper
          elevation={3}
          sx={{
            p: 3,
            mb: 3,
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, justifyContent: "space-between" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <TableChartIcon sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h4" fontWeight="bold">
                  Semantic AI Platform
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Ask questions in natural language and get instant SQL insights
                </Typography>
              </Box>
            </Box>
            {/* <Button
              variant="outlined"
              startIcon={<BookmarkIcon />}
              onClick={() => setSidebarOpen(true)}
              sx={{
                color: "white",
                borderColor: "white",
                "&:hover": {
                  borderColor: "white",
                  bgcolor: "rgba(255,255,255,0.1)",
                },
              }}
            >
              Saved Reports
            </Button> */}
          </Box>
        </Paper>

        {/* Query Input */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          {/* Report Name Display */}
          {currentReportName && (
            <Box sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}>
              <BookmarkIcon color="primary" />
              <Typography variant="body2" color="text.secondary">
                Viewing Report:
              </Typography>
              <Chip 
                label={currentReportName} 
                color="primary" 
                variant="outlined"
                onDelete={() => {
                  setCurrentReportName("");
                  setQuestion("");
                  setSql("");
                  setRows([]);
                }}
                sx={{ fontWeight: "bold" }}
              />
            </Box>
          )}
          
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Ask Your Question
          </Typography>
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., Show me handler-wise sales summary with customer count..."
              variant="outlined"
              disabled={loading}
              sx={{ bgcolor: "white" }}
            />
            <Button
              variant="contained"
              size="large"
              onClick={ask}
              disabled={loading || !question.trim()}
              endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              sx={{
                minWidth: 120,
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "&:hover": {
                  background: "linear-gradient(135deg, #764ba2 0%, #667eea 100%)",
                },
              }}
            >
              {loading ? "Thinking..." : "Ask"}
            </Button>
          </Box>
        </Paper>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError("")}>
            <Typography variant="body2">{error}</Typography>
          </Alert>
        )}
        {/* Warning Display */}
        {warning && (
          <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setWarning("")}>
            <Typography variant="body2">{warning}</Typography>
          </Alert>
        )}

        {/* SQL Display */}
        {sql && (
          <Card sx={{ mb: 3 }} elevation={2}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <CodeIcon color="primary" />
                  <Typography variant="h6">Generated SQL</Typography>
                </Box>
                <Chip
                  label={`${rows.length} rows`}
                  color="primary"
                  size="small"
                  variant="outlined"
                />
              </Box>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  bgcolor: "#f8f9fa",
                  border: "1px solid #e0e0e0",
                  borderRadius: 1,
                  overflow: "auto",
                }}
              >
                <Typography
                  component="pre"
                  sx={{
                    fontFamily: "monospace",
                    fontSize: "0.875rem",
                    margin: 0,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {sql}
                </Typography>
              </Paper>
            </CardContent>
          </Card>
        )}

        {/* No Data Found Alert */}
        {sql && rows.length === 0 && !loading && !error && showNoDataAlert && (
          <Alert 
            severity="info" 
            sx={{ mb: 3 }}
            onClose={() => setShowNoDataAlert(false)}
          >
            <Typography variant="body1" fontWeight="bold" gutterBottom>
              No Data Found
            </Typography>
            <Typography variant="body2">
              The query executed successfully but returned no results. This could mean:
              <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                <li>No records match your query criteria</li>
                <li>The filters are too restrictive</li>
                <li>The data may not exist for the selected parameters</li>
              </ul>
              Try adjusting your question or filters to get results.
            </Typography>
          </Alert>
        )}

        {/* Results Table */}
        {rows.length > 0 && (
          <Paper elevation={2}>
            <Box sx={{ p: 2, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 2 }}>
              <Typography variant="h6">
                {currentReportName ? `${currentReportName} - Results` : "Query Results"}
              </Typography>
              <Box sx={{ display: "flex", gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={openSaveDialog}
                  sx={{
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "&:hover": {
                      background: "linear-gradient(135deg, #764ba2 0%, #667eea 100%)",
                    },
                  }}
                >
                  Save Report
                </Button>
                <Button
                  variant="contained"
                  startIcon={<PieChartIcon />}
                  onClick={openVisualization}
                  sx={{
                    background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                    "&:hover": {
                      background: "linear-gradient(135deg, #f5576c 0%, #f093fb 100%)",
                    },
                  }}
                >
                  Visualize
                </Button>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={downloadExcel}
                  color="success"
                >
                  Export to Excel
                </Button>
              </Box>
            </Box>
            <Divider />
            
            <TableContainer sx={{ maxHeight: 600 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    {columns.map((col) => (
                      <TableCell
                        key={col}
                        sx={{
                          bgcolor: "#667eea",
                          color: "white",
                          fontWeight: "bold",
                          textTransform: "uppercase",
                          fontSize: "0.875rem",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {col}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedRows.map((row, idx) => (
                    <TableRow
                      key={idx}
                      hover
                      sx={{
                        "&:nth-of-type(odd)": { bgcolor: "#f9f9f9" },
                        "&:hover": { bgcolor: "#e3f2fd !important" },
                      }}
                    >
                      {columns.map((col) => (
                        <TableCell
                          key={col}
                          sx={{
                            whiteSpace: "nowrap",
                            fontSize: "0.875rem",
                          }}
                        >
                          {row[col] !== null && row[col] !== undefined
                            ? String(row[col])
                            : <span style={{ color: "#999", fontStyle: "italic" }}>null</span>}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              rowsPerPageOptions={[5, 10, 25, 50, 100]}
              component="div"
              count={rows.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              sx={{ borderTop: "1px solid #e0e0e0" }}
            />
          </Paper>
        )}

        {/* Empty State */}
        {!loading && !sql && !error && (
          <Paper
            elevation={1}
            sx={{
              p: 6,
              textAlign: "center",
              bgcolor: "#fafafa",
              border: "2px dashed #e0e0e0",
            }}
          >
            <TableChartIcon sx={{ fontSize: 64, color: "#bdbdbd", mb: 2 }} />
            <Typography variant="h6" color="textSecondary" gutterBottom>
              No queries yet
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Ask a question to see results
            </Typography>
          </Paper>
        )}

        {/* Visualization Modal */}
        <Dialog 
          open={openViz} 
          onClose={closeVisualization}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle sx={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", color: "white" }}>
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <PieChartIcon />
                <Typography variant="h6">Create Visualization</Typography>
              </Box>
              <CloseIcon sx={{ cursor: "pointer" }} onClick={closeVisualization} />
            </Box>
          </DialogTitle>
          
          <DialogContent sx={{ mt: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Category Column (for slices)</InputLabel>
                  <Select
                    value={categoryColumn}
                    label="Category Column (for slices)"
                    onChange={(e) => setCategoryColumn(e.target.value)}
                  >
                    {categoricalColumns.map(col => (
                      <MenuItem key={col} value={col}>{col}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Value Column (to aggregate)</InputLabel>
                  <Select
                    value={valueColumn}
                    label="Value Column (to aggregate)"
                    onChange={(e) => setValueColumn(e.target.value)}
                  >
                    {numericalColumns.map(col => (
                      <MenuItem key={col} value={col}>{col}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Aggregation Method</InputLabel>
                  <Select
                    value={aggregation}
                    label="Aggregation Method"
                    onChange={(e) => setAggregation(e.target.value)}
                  >
                    <MenuItem value="SUM">SUM (Total)</MenuItem>
                    <MenuItem value="AVG">AVG (Average)</MenuItem>
                    <MenuItem value="COUNT">COUNT (Number of records)</MenuItem>
                    <MenuItem value="MAX">MAX (Highest value)</MenuItem>
                    <MenuItem value="MIN">MIN (Lowest value)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Show Top</InputLabel>
                  <Select
                    value={topN}
                    label="Show Top"
                    onChange={(e) => setTopN(e.target.value)}
                  >
                    <MenuItem value={5}>Top 5</MenuItem>
                    <MenuItem value={10}>Top 10</MenuItem>
                    <MenuItem value={15}>Top 15</MenuItem>
                    <MenuItem value={20}>Top 20</MenuItem>
                    <MenuItem value={999}>All</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            {categoryColumn && valueColumn && (
              <Box ref={chartRef} sx={{ mt: 4, p: 3, bgcolor: "white" }}>
                <Typography variant="h6" align="center" gutterBottom>
                  {aggregation} of {valueColumn} by {categoryColumn}
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name}: ${percentage}%`}
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            )}
          </DialogContent>
          
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={closeVisualization}>Close</Button>
            {chartData.length > 0 && (
              <Button
                variant="contained"
                startIcon={<ImageIcon />}
                onClick={downloadChart}
                color="success"
              >
                Download PNG
              </Button>
            )}
          </DialogActions>
        </Dialog>

        {/* Save Report Dialog */}
        <Dialog
          open={saveDialogOpen}
          onClose={closeSaveDialog}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle sx={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", color: "white" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <SaveIcon />
              <Typography variant="h6">Save Report</Typography>
            </Box>
          </DialogTitle>
          
          <DialogContent sx={{ mt: 3 }}>
            <TextField
              fullWidth
              label="Report Name *"
              value={reportName}
              onChange={(e) => setReportName(e.target.value)}
              placeholder="e.g., Monthly Sales Summary"
              sx={{ mb: 3 }}
              autoFocus
            />
            
            <TextField
              fullWidth
              label="Description (optional)"
              value={reportDescription}
              onChange={(e) => setReportDescription(e.target.value)}
              placeholder="What does this report show?"
              multiline
              rows={3}
              sx={{ mb: 3 }}
            />
            
            <TextField
              fullWidth
              label="Tags (optional)"
              value={reportTags}
              onChange={(e) => setReportTags(e.target.value)}
              placeholder="sales, monthly, executive (comma separated)"
              helperText="Add tags to organize and find your reports easily"
            />
            
            <Box sx={{ mt: 3, p: 2, bgcolor: "#f5f7fa", borderRadius: 1 }}>
              <Typography variant="caption" color="textSecondary">
                This will save:
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                • Question: {question.substring(0, 80)}{question.length > 80 ? '...' : ''}
              </Typography>
              <Typography variant="body2">
                • SQL Query: {rows.length} rows returned
              </Typography>
            </Box>
          </DialogContent>
          
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={closeSaveDialog}>Cancel</Button>
            <Button
              variant="contained"
              onClick={saveReport}
              disabled={!reportName.trim()}
              sx={{
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              }}
            >
              Save Report
            </Button>
          </DialogActions>
        </Dialog>

        {/* Footer */}
        <Box sx={{ mt: 4, textAlign: "center" }}>
          <Typography variant="body2" color="textSecondary">
            Powered by Groq AI · Built with Material-UI & Recharts
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}
