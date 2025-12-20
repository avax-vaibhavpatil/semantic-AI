import React, { useState, useEffect } from "react";
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  IconButton,
  Chip,
  Divider,
  TextField,
  InputAdornment,
  Tooltip,
  CircularProgress,
  Alert,
  Badge,
} from "@mui/material";
import {
  BookmarkBorder as BookmarkIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Search as SearchIcon,
  Close as CloseIcon,
  PlayArrow as ExecuteIcon,
  Delete as DeleteIcon,
  CalendarToday as DateIcon,
} from "@mui/icons-material";
import axios from "axios";

const DRAWER_WIDTH = 360;

export default function SavedReportsSidebar({ open, onClose, onExecuteReport }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterFavorites, setFilterFavorites] = useState(false);

  // Load reports when sidebar opens
  useEffect(() => {
    if (open) {
      loadReports();
    }
  }, [open]);

  const loadReports = async () => {
    setLoading(true);
    setError("");
    try {
      const params = {};
      if (filterFavorites) {
        params.favorite_only = true;
      }
      
      const res = await axios.get("http://localhost:8000/reports", { params });
      setReports(res.data.reports || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load reports");
    }
    setLoading(false);
  };

  const searchReports = async (query) => {
    if (!query.trim()) {
      loadReports();
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`http://localhost:8000/reports/search`, {
        params: { q: query, limit: 50 }
      });
      setReports(res.data.reports || []);
    } catch (err) {
      setError("Search failed");
    }
    setLoading(false);
  };

  const toggleFavorite = async (reportId, currentFavorite) => {
    try {
      await axios.patch(`http://localhost:8000/reports/${reportId}`, {
        is_favorite: !currentFavorite
      });
      
      // Update local state
      setReports(reports.map(r => 
        r.report_id === reportId 
          ? { ...r, is_favorite: !currentFavorite }
          : r
      ));
    } catch (err) {
      console.error("Failed to toggle favorite:", err);
    }
  };

  const deleteReport = async (reportId) => {
    if (!confirm("Are you sure you want to delete this report?")) return;
    
    try {
      await axios.delete(`http://localhost:8000/reports/${reportId}`);
      setReports(reports.filter(r => r.report_id !== reportId));
    } catch (err) {
      console.error("Failed to delete report:", err);
    }
  };

  const executeReport = async (report) => {
    try {
      const res = await axios.post(
        `http://localhost:8000/reports/${report.report_id}/execute`
      );
      
      // Pass data back to parent component
      if (onExecuteReport) {
        onExecuteReport({
          reportName: report.report_name,
          userQuestion: res.data.report.user_question,  // ← ADD THIS!
          reportDescription: res.data.report.report_description,
          sql: res.data.report.generated_sql,
          rows: res.data.rows,
          executionTime: res.data.execution_time_ms
        });
      }
      
      // Refresh the list to update execution count
      loadReports();
      
      // Close sidebar (optional)
      // onClose();
    } catch (err) {
      console.error("Failed to execute report:", err);
      alert("Failed to execute report: " + (err.response?.data?.detail || err.message));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Debounce search
    if (searchTimeout) clearTimeout(searchTimeout);
    const timeout = setTimeout(() => {
      searchReports(query);
    }, 500);
    setSearchTimeout(timeout);
  };

  const [searchTimeout, setSearchTimeout] = useState(null);

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: DRAWER_WIDTH,
          boxSizing: "border-box",
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <BookmarkIcon />
          <Typography variant="h6" fontWeight="bold">
            Saved Reports
          </Typography>
          {reports.length > 0 && (
            <Chip 
              label={reports.length} 
              size="small" 
              sx={{ 
                bgcolor: "rgba(255,255,255,0.3)", 
                color: "white",
                fontWeight: "bold"
              }} 
            />
          )}
        </Box>
        <IconButton onClick={onClose} sx={{ color: "white" }} size="small">
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Search & Filters */}
      <Box sx={{ p: 2, bgcolor: "#f5f7fa" }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search reports..."
          value={searchQuery}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: searchQuery && (
              <InputAdornment position="end">
                <IconButton
                  size="small"
                  onClick={() => {
                    setSearchQuery("");
                    loadReports();
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ bgcolor: "white", mb: 1 }}
        />
        
        <Box sx={{ display: "flex", gap: 1 }}>
          <Chip
            icon={<StarIcon />}
            label="Favorites"
            onClick={() => {
              setFilterFavorites(!filterFavorites);
              setTimeout(() => loadReports(), 100);
            }}
            color={filterFavorites ? "primary" : "default"}
            variant={filterFavorites ? "filled" : "outlined"}
            size="small"
          />
        </Box>
      </Box>

      <Divider />

      {/* Reports List */}
      <Box sx={{ flex: 1, overflow: "auto", bgcolor: "#fafafa" }}>
        {loading && (
          <Box sx={{ p: 4, textAlign: "center" }}>
            <CircularProgress size={40} />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
              Loading reports...
            </Typography>
          </Box>
        )}

        {error && (
          <Box sx={{ p: 2 }}>
            <Alert severity="error" onClose={() => setError("")}>
              {error}
            </Alert>
          </Box>
        )}

        {!loading && !error && reports.length === 0 && (
          <Box sx={{ p: 4, textAlign: "center" }}>
            <BookmarkIcon sx={{ fontSize: 64, color: "#bdbdbd", mb: 2 }} />
            <Typography variant="body1" color="textSecondary" gutterBottom>
              No saved reports yet
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Save your queries to access them later
            </Typography>
          </Box>
        )}

        {!loading && !error && reports.length > 0 && (
          <List sx={{ p: 0 }}>
            {reports.map((report) => (
              <Box
                key={report.report_id}
                sx={{
                  borderBottom: "1px solid #e0e0e0",
                  bgcolor: "white",
                  mb: 0.5,
                  transition: "all 0.2s",
                  "&:hover": {
                    bgcolor: "#f5f7fa",
                    transform: "translateX(2px)",
                  },
                }}
              >
                <ListItem
                  disablePadding
                  secondaryAction={
                    <Box sx={{ display: "flex", gap: 0.5 }}>
                      <Tooltip title={report.is_favorite ? "Remove from favorites" : "Add to favorites"}>
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(report.report_id, report.is_favorite);
                          }}
                        >
                          {report.is_favorite ? (
                            <StarIcon sx={{ color: "#FFD700" }} />
                          ) : (
                            <StarBorderIcon />
                          )}
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Delete report">
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteReport(report.report_id);
                          }}
                          sx={{ color: "#f44336" }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  }
                >
                  <ListItemButton
                    onClick={() => executeReport(report)}
                    sx={{ pr: 10 }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      <ExecuteIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography variant="body2" fontWeight="bold" noWrap>
                          {report.report_name}
                        </Typography>
                      }
                      secondary={
                        <Box sx={{ mt: 0.5 }}>
                          {report.tags && report.tags.length > 0 && (
                            <Box sx={{ display: "flex", gap: 0.5, mb: 0.5, flexWrap: "wrap" }}>
                              {report.tags.slice(0, 2).map((tag) => (
                                <Chip
                                  key={tag}
                                  label={tag}
                                  size="small"
                                  sx={{
                                    height: 18,
                                    fontSize: "0.7rem",
                                    bgcolor: "#e3f2fd",
                                    color: "#1976d2",
                                  }}
                                />
                              ))}
                              {report.tags.length > 2 && (
                                <Chip
                                  label={`+${report.tags.length - 2}`}
                                  size="small"
                                  sx={{
                                    height: 18,
                                    fontSize: "0.7rem",
                                  }}
                                />
                              )}
                            </Box>
                          )}
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                            <Typography variant="caption" color="textSecondary">
                              <DateIcon sx={{ fontSize: 12, verticalAlign: "middle", mr: 0.5 }} />
                              {formatDate(report.created_at)}
                            </Typography>
                          </Box>
                          {report.execution_count > 0 && (
                            <Typography variant="caption" color="primary">
                              Executed {report.execution_count} time{report.execution_count > 1 ? 's' : ''}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              </Box>
            ))}
          </List>
        )}
      </Box>

      {/* Footer */}
      <Divider />
      <Box sx={{ p: 2, bgcolor: "#f5f7fa", textAlign: "center" }}>
        <Typography variant="caption" color="textSecondary">
          Click any report to execute it
        </Typography>
      </Box>
    </Drawer>
  );
}

